import unittest
from code.gemini_provider import GeminiLLMProvider

class TestGeminiProvider(unittest.TestCase):
    def test_missing_api_key_raises_error(self):
        class MockGeminiProvider(GeminiLLMProvider):
            def _load_api_key_from_env(self):
                return None
                
        with self.assertRaises(ValueError) as context:
            MockGeminiProvider(api_key=None)
            
        self.assertIn("GEMINI_API_KEY not found", str(context.exception))

    def test_initialization_with_key(self):
        provider = GeminiLLMProvider(api_key="fake_key_for_test")
        self.assertEqual(provider.model, "gemini-3.5-flash-lite")
        self.assertEqual(provider.usage["calls"], 0)

if __name__ == "__main__":
    unittest.main()
