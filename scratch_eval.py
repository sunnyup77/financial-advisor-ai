import csv
import os
from datetime import date
from collections import defaultdict
from code.models import RequestData
from code.data_loader import DataLoader
from code.gemini_provider import GeminiLLMProvider
from code.llm_extractor import EvidenceExtractor
from code.pipeline import Pipeline
import time

def evaluate():
    loader = DataLoader()
    loader.load_all()
    
    provider = GeminiLLMProvider()
    extractor = EvidenceExtractor(provider)
    pipeline = Pipeline(loader, extractor)
    
    total_samples = 0
    exact_matches = 0
    
    start_time = time.time()
    
    # We will hook into the extractor's cache checking to count hits and misses
    original_read = extractor._read_cache
    cache_hits = 0
    cache_misses = 0
    
    def hooked_read(cache_key):
        nonlocal cache_hits, cache_misses
        res = original_read(cache_key)
        if res:
            cache_hits += 1
        else:
            cache_misses += 1
        return res
        
    extractor._read_cache = hooked_read
    
    with open(os.path.join("INFO", "dataset", "sample_requests.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 20:
                break
            total_samples += 1
            req = RequestData(
                request_id=row["request_id"],
                user_id=row["user_id"],
                request_date=date.fromisoformat(row["request_date"]),
                request_type=row["request_type"],
                requested_amount=float(row["requested_amount"]),
                desired_completion_date=date.fromisoformat(row["desired_completion_date"]),
                allows_partial_payment=(row["allows_partial_payment"].lower() == 'true'),
                request_text=row["request_text"]
            )
            pipeline.process_request(req)
            
    end_time = time.time()
    
    usage = provider.get_usage()
    print("--- METRICS ---")
    print(f"Runtime: {end_time - start_time:.2f} seconds")
    print(f"API Calls Made: {usage['calls']}")
    print(f"Cache Hits: {cache_hits}")
    print(f"Cache Misses: {cache_misses}")

if __name__ == '__main__':
    evaluate()
