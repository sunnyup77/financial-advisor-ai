import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from code.llm_extractor import LLMProvider

class NvidiaLLMProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "meta/llama3-70b-instruct"):
        self.model = model
        self.endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.api_key = api_key or self._load_api_key_from_env()
        
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY not found in environment or .env file")
            
        self.usage = {
            "model": self.model,
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0
        }

    def _load_api_key_from_env(self) -> Optional[str]:
        # Try OS env first
        if "NVIDIA_API_KEY" in os.environ:
            return os.environ["NVIDIA_API_KEY"]
            
        # Try loading from .env
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("NVIDIA_API_KEY="):
                        val = line.split("=", 1)[1]
                        return val.strip('"\'')
        return None

    def generate_json(self, prompt: str, image_path: Optional[str] = None) -> str:
        # Note: image_path handling is omitted for this simple text connection test.
        # It can be added later if multi-modal is required for Kimi-K3 via the same endpoint.
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.0
        }
        
        req = urllib.request.Request(
            self.endpoint, 
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                resp_body = response.read().decode('utf-8')
                data = json.loads(resp_body)
                
                # Update usage stats
                self.usage["calls"] += 1
                usage_info = data.get("usage", {})
                self.usage["input_tokens"] += usage_info.get("prompt_tokens", 0)
                self.usage["output_tokens"] += usage_info.get("completion_tokens", 0)
                self.usage["total_tokens"] += usage_info.get("total_tokens", 0)
                
                content = data["choices"][0]["message"]["content"]
                return content
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            raise RuntimeError(f"NVIDIA API HTTP Error {e.code}: {err_body}")
        except Exception as e:
            raise RuntimeError(f"NVIDIA API Error: {str(e)}")

    def get_usage(self) -> Dict[str, Any]:
        return self.usage
