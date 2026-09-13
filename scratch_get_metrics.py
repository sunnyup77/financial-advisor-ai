import os
import glob
from code.data_loader import DataLoader
from code.gemini_provider import GeminiLLMProvider
from code.llm_extractor import EvidenceExtractor

def count_cache():
    cache_dir = ".cache"
    if not os.path.exists(cache_dir):
        return 0
    return len(glob.glob(os.path.join(cache_dir, "*.json")))

print(f"Total files in cache: {count_cache()}")
