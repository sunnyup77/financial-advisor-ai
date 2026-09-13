import unittest
from code.nvidia_provider import NvidiaLLMProvider

class TestNvidiaProvider(unittest.TestCase):
    def test_missing_api_key_raises_error(self):
        # Temporarily mock the env loading to return None
        class MockNvidiaProvider(NvidiaLLMProvider):
            def _load_api_key_from_env(self):
                return None
                
        with self.assertRaises(ValueError) as context:
            MockNvidiaProvider(api_key=None)
            
        self.assertIn("NVIDIA_API_KEY not found", str(context.exception))

    def test_initialization_with_key(self):
        provider = NvidiaLLMProvider(api_key="fake_key_for_test")
        self.assertEqual(provider.model, "meta/llama3-70b-instruct")
        self.assertEqual(provider.usage["calls"], 0)

if __name__ == "__main__":
    unittest.main()
