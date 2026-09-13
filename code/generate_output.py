import csv
import os
import time
import argparse
from typing import Dict, Any

from code.data_loader import DataLoader
from code.gemini_provider import GeminiLLMProvider
from code.llm_extractor import EvidenceExtractor
from code.pipeline import Pipeline

def run_production(limit: int = None):
    # Instrumentation variables
    cache_hits = 0
    cache_misses = 0
    api_429_count = 0
    api_503_count = 0
    api_timeout_count = 0
    api_success_count = 0
    api_failed_count = 0
    
    print("Loading data...")
    loader = DataLoader()
    loader.load_all()
    
    provider = GeminiLLMProvider()
    extractor = EvidenceExtractor(provider)
    pipeline = Pipeline(loader, extractor)
    
    # Monkey-patch EvidenceExtractor to count cache hits/misses
    original_read_cache = extractor._read_cache
    def hooked_read_cache(cache_key: str):
        nonlocal cache_hits, cache_misses
        res = original_read_cache(cache_key)
        if res:
            cache_hits += 1
        else:
            cache_misses += 1
        return res
    extractor._read_cache = hooked_read_cache
    
    # Monkey-patch provider's generate_json to count errors
    original_generate_json = provider.generate_json
    def hooked_generate_json(prompt: str, image_path: str = None, schema: dict = None):
        nonlocal api_429_count, api_503_count, api_timeout_count, api_success_count, api_failed_count
        try:
            res = original_generate_json(prompt, image_path, schema)
            api_success_count += 1
            return res
        except Exception as e:
            api_failed_count += 1
            err_str = str(e).lower()
            if "429" in err_str:
                api_429_count += 1
            elif "503" in err_str:
                api_503_count += 1
            elif "timeout" in err_str:
                api_timeout_count += 1
            raise e
    provider.generate_json = hooked_generate_json
    
    requests_to_process = loader.requests
    if limit is not None:
        requests_to_process = requests_to_process[:limit]
        
    num_requests = len(requests_to_process)
    
    output_rows = []
    seen_ids = set()
    
    start_time = time.time()
    for i, req in enumerate(requests_to_process):
        print(f"Processing {i+1}/{num_requests}: {req.request_id}")
        try:
            decision = pipeline.process_request(req)
            output_rows.append({
                "request_id": decision.request_id,
                "amount_safe_to_pay": decision.amount_safe_to_pay,
                "affordability_status": decision.affordability_status,
                "recommended_payment_method": decision.recommended_payment_method,
                "payment_plan": decision.payment_plan,
                "earliest_date_for_full_payment": decision.earliest_date_for_full_payment,
                "spending_changes_needed": decision.spending_changes_needed,
                "decision_explanation": decision.decision_explanation
            })
            if decision.request_id in seen_ids:
                raise ValueError(f"Duplicate request_id found in output: {decision.request_id}")
            seen_ids.add(decision.request_id)
        except Exception as e:
            print(f"ERROR processing {req.request_id}: {e}")
            raise e
            
    end_time = time.time()
    runtime = end_time - start_time
    
    # Write output.csv
    headers = [
        "request_id",
        "amount_safe_to_pay",
        "affordability_status",
        "recommended_payment_method",
        "payment_plan",
        "earliest_date_for_full_payment",
        "spending_changes_needed",
        "decision_explanation"
    ]
    
    output_path = "output.csv"
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(output_rows)
        
    print(f"\nFinal output written to: {output_path}")
    
    # Validation Checks
    assert os.path.exists(output_path), "output.csv was not created"
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        actual_headers = next(reader)
        assert actual_headers == headers, f"Headers do not match. Expected {headers}, got {actual_headers}"
        row_count = sum(1 for row in reader)
        assert row_count == num_requests, f"Row count {row_count} does not match input count {num_requests}"
        
    # Write usage report
    usage = provider.get_usage()
    report_path = os.path.join("evaluation", "usage_report.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Final Production Usage Report\n\n")
        f.write(f"- Provider: Gemini REST API\n")
        f.write(f"- Model: {usage['model']}\n")
        f.write(f"- Total API calls: {usage['calls']}\n")
        f.write(f"- Successful calls: {api_success_count}\n")
        f.write(f"- Failed calls: {api_failed_count}\n")
        f.write(f"- Cache hits: {cache_hits}\n")
        f.write(f"- Cache misses: {cache_misses}\n")
        f.write(f"- 429 count: {api_429_count}\n")
        f.write(f"- 503 count: {api_503_count}\n")
        f.write(f"- Timeout count: {api_timeout_count}\n")
        f.write(f"- Input tokens: {usage['input_tokens']}\n")
        f.write(f"- Output tokens: {usage['output_tokens']}\n")
        f.write(f"- Total tokens: {usage['total_tokens']}\n")
        f.write(f"- Estimated cost: ${usage['estimated_cost']:.2f}\n")
        f.write(f"- Number of requests processed: {num_requests}\n")
        f.write(f"- Runtime: {runtime:.2f} seconds\n")
        
    print(f"Usage report written to: {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate final production output for all requests")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for testing. Default processes ALL 250 requests.")
    args = parser.parse_args()
    
    run_production(limit=args.limit)
