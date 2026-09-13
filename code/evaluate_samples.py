import csv
import os
from datetime import date
from collections import defaultdict
from code.models import RequestData
from code.data_loader import DataLoader
from code.gemini_provider import GeminiLLMProvider
from code.llm_extractor import EvidenceExtractor
from code.pipeline import Pipeline

def evaluate():
    loader = DataLoader()
    loader.load_all()
    
    provider = GeminiLLMProvider()
    extractor = EvidenceExtractor(provider)
    pipeline = Pipeline(loader, extractor)
    
    sample_path = os.path.join("INFO", "dataset", "sample_requests.csv")
    
    results = []
    mismatches = defaultdict(list)
    total_samples = 0
    exact_matches = 0
    
    fields_to_compare = [
        "amount_safe_to_pay",
        "affordability_status",
        "recommended_payment_method",
        "payment_plan",
        "earliest_date_for_full_payment",
        "spending_changes_needed",
        "decision_explanation"
    ]
    
    with open(sample_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_samples += 1
            # Parse request
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
            
            # Get expected
            expected = {k: row[k] for k in fields_to_compare}
            
            # Run pipeline
            decision = pipeline.process_request(req)
            
            # Get actual
            actual = {
                "amount_safe_to_pay": decision.amount_safe_to_pay,
                "affordability_status": decision.affordability_status,
                "recommended_payment_method": decision.recommended_payment_method,
                "payment_plan": decision.payment_plan,
                "earliest_date_for_full_payment": decision.earliest_date_for_full_payment,
                "spending_changes_needed": decision.spending_changes_needed,
                "decision_explanation": decision.decision_explanation
            }
            
            is_exact = True
            for fld in fields_to_compare:
                if str(actual[fld]) != str(expected[fld]):
                    is_exact = False
                    mismatches[fld].append({
                        "request_id": req.request_id,
                        "expected": expected[fld],
                        "actual": actual[fld]
                    })
            
            if is_exact:
                exact_matches += 1
                
    # Write report
    os.makedirs("evaluation", exist_ok=True)
    with open("evaluation/sample_evaluation.md", "w", encoding="utf-8") as f:
        f.write("# Sample Evaluation Report\n\n")
        f.write(f"- Total Samples: {total_samples}\n")
        f.write(f"- Exact Matches: {exact_matches}\n")
        f.write(f"- Total Mismatches: {total_samples - exact_matches}\n\n")
        
        f.write("## Field-Level Accuracy\n")
        for fld in fields_to_compare:
            miss_count = len(mismatches[fld])
            acc = ((total_samples - miss_count) / total_samples) * 100
            f.write(f"- **{fld}**: {acc:.1f}% ({total_samples - miss_count}/{total_samples})\n")
            
        f.write("\n## Mismatches by Field\n")
        for fld in fields_to_compare:
            if mismatches[fld]:
                f.write(f"\n### {fld}\n")
                for m in mismatches[fld]:
                    f.write(f"- **{m['request_id']}**\n")
                    f.write(f"  - Expected: `{m['expected']}`\n")
                    f.write(f"  - Actual: `{m['actual']}`\n")
                    f.write(f"  - Reason: TODO\n")
                    
        f.write("\n## Gemini API Usage\n")
        usage = provider.get_usage()
        f.write(f"- Provider: Gemini REST API (gemini-3-flash-preview)\n")
        f.write(f"- Input Tokens: {usage['input_tokens']}\n")
        f.write(f"- Output Tokens: {usage['output_tokens']}\n")
        f.write(f"- Total Tokens: {usage['total_tokens']}\n")
        
if __name__ == '__main__':
    evaluate()
