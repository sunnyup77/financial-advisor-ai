import os
import json
import time
from code.gemini_provider import GeminiLLMProvider

def run_integration_test():
    print("--- Starting Gemini API Integration Test ---")
    try:
        provider = GeminiLLMProvider()
        print(f"Provider initialized successfully with model: {provider.model}")
        
        # Test 1: Minimal text test with dummy schema
        # We use a dummy schema so that the model returns exactly the requested string in JSON
        prompt = "Reply with exactly: Gemini connection successful"
        print(f"\n--- Test 1: Minimal Connection ---")
        print(f"Sending prompt: '{prompt}'")
        
        tiny_schema = {
            "type": "OBJECT",
            "properties": {
                "response": {"type": "STRING"}
            },
            "required": ["response"]
        }
        
        start_time = time.time()
        response1 = provider.generate_json(prompt, schema=tiny_schema)
        latency1 = time.time() - start_time
        
        print(f"API Response (Latency: {latency1:.2f}s):")
        print(response1)
        
        # Test 2: Structured output test
        print(f"\n--- Test 2: Structured Output ---")
        structured_prompt = "Return a successful status and a message saying Gemini structured output works."
        
        structured_schema = {
            "type": "OBJECT",
            "properties": {
                "status": {"type": "STRING"},
                "message": {"type": "STRING"}
            },
            "required": ["status", "message"]
        }
        
        start_time = time.time()
        response2 = provider.generate_json(structured_prompt, schema=structured_schema)
        latency2 = time.time() - start_time
        
        print(f"API Response (Latency: {latency2:.2f}s):")
        print(response2)
        
        print("\n--- API Usage ---")
        print(json.dumps(provider.get_usage(), indent=2))
        
        if "Gemini connection successful" in response1 and "Gemini structured output works" in response2:
            print("\nINTEGRATION TEST PASSED!")
        else:
            print("\nINTEGRATION TEST FAILED: Response mismatch.")
            
    except Exception as e:
        print(f"\nINTEGRATION TEST FAILED WITH ERROR: {str(e)}")

if __name__ == "__main__":
    run_integration_test()
