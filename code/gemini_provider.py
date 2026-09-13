import os
import json
import urllib.request
import urllib.error
import base64
import mimetypes
from typing import Dict, Any, Optional
from code.llm_extractor import LLMProvider

# The expected Phase 2 schema
EXTRACTED_FACT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "extracted_facts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "fact_type": {"type": "STRING"},
                    "affected_event_id": {"type": "STRING", "nullable": True},
                    "affected_request_id": {"type": "STRING", "nullable": True},
                    "new_amount": {"type": "NUMBER", "nullable": True},
                    "new_date": {"type": "STRING", "nullable": True},
                    "confidence": {"type": "STRING"},
                    "requires_deterministic_validation": {"type": "BOOLEAN"}
                },
                "required": ["fact_type", "confidence", "requires_deterministic_validation"]
            }
        }
    },
    "required": ["extracted_facts"]
}

class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3.5-flash-lite"):
        self.model = model
        self.api_key = api_key or self._load_api_key_from_env()
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or .env file")
            
        self.usage = {
            "model": self.model,
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0
        }

    def _load_api_key_from_env(self) -> Optional[str]:
        if "GEMINI_API_KEY" in os.environ:
            return os.environ["GEMINI_API_KEY"]
            
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.split("=", 1)[1]
                        return val.strip('"\'')
        return None

    def generate_json(self, prompt: str, image_path: Optional[str] = None, schema: Optional[Dict] = None) -> str:
        # Default to the Phase 2 schema if none provided
        active_schema = schema if schema is not None else EXTRACTED_FACT_SCHEMA
        
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        parts = [{"text": prompt}]
        
        if image_path and os.path.exists(image_path):
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                mime_type = "image/jpeg"
            with open(image_path, "rb") as img_f:
                b64_data = base64.b64encode(img_f.read()).decode('utf-8')
            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": b64_data
                }
            })
            
        payload = {
            "contents": [{
                "parts": parts
            }],
            "generationConfig": {
                "temperature": 0.0,
                "response_mime_type": "application/json",
                "response_schema": active_schema
            }
        }
        
        import time
        max_retries = 5
        for attempt in range(max_retries):
            req = urllib.request.Request(
                endpoint, 
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method='POST'
            )
            
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    resp_body = response.read().decode('utf-8')
                    data = json.loads(resp_body)
                    
                    self.usage["calls"] += 1
                    usage_meta = data.get("usageMetadata", {})
                    self.usage["input_tokens"] += usage_meta.get("promptTokenCount", 0)
                    self.usage["output_tokens"] += usage_meta.get("candidatesTokenCount", 0)
                    self.usage["total_tokens"] += usage_meta.get("totalTokenCount", 0)
                    
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    return content
            except urllib.error.HTTPError as e:
                err_body = e.read().decode('utf-8')
                if e.code == 429 and attempt < max_retries - 1:
                    # Check if it's a daily quota exhaustion
                    if "GenerateRequestsPerDay" in err_body:
                        raise RuntimeError(f"Gemini API Daily Quota Exhausted: {err_body}")
                    print(f"429 Rate Limit Hit. Attempt {attempt+1}/{max_retries}. Sleeping {15 * (attempt + 1)}s...")
                    time.sleep(15 * (attempt + 1))
                    continue
                raise RuntimeError(f"Gemini API HTTP Error {e.code}: {err_body}")
            except Exception as e:
                raise RuntimeError(f"Gemini API Error: {str(e)}")

    def get_usage(self) -> Dict[str, Any]:
        return self.usage
