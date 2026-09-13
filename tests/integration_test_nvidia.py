import os
import json
import time
from code.nvidia_provider import NvidiaLLMProvider

def run_integration_test():
    print("--- Starting NVIDIA NIM Integration Test ---")
    try:
        # Initialize the provider (will load from .env automatically)
        provider = NvidiaLLMProvider()
        print(f"Provider initialized successfully with model: {provider.model}")
        print(f"Endpoint: {provider.endpoint}")
        
        prompt = "Reply with exactly: NVIDIA connection successful"
        print(f"\nSending prompt: '{prompt}'")
        
        # Make the real API call
        start_time = time.time()
        response = provider.generate_json(prompt)
        latency = time.time() - start_time
        
        print(f"\n--- API Response (Latency: {latency:.2f}s) ---")
        print(response)
        
        print("\n--- API Usage ---")
        usage = provider.get_usage()
        # Redact the actual cost info logic here since we just track tokens
        print(json.dumps(usage, indent=2))
        
        if "NVIDIA connection successful" in response:
            print("\nINTEGRATION TEST PASSED!")
        else:
            print("\nINTEGRATION TEST FAILED: Response did not contain expected text.")
            
    except Exception as e:
        print(f"\nINTEGRATION TEST FAILED WITH ERROR: {str(e)}")

if __name__ == "__main__":
    run_integration_test()
