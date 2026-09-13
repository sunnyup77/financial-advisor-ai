import csv
import re
import os

def validate():
    print("--- VALIDATION SCRIPT START ---")
    output_path = "output.csv"
    requests_path = "INFO/dataset/requests.csv"
    report_path = "evaluation/usage_report.md"
    
    # Check 1: Header
    expected_header = ["request_id", "amount_safe_to_pay", "affordability_status", "recommended_payment_method", "payment_plan", "earliest_date_for_full_payment", "spending_changes_needed", "decision_explanation"]
    
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            actual_header = next(reader)
            if actual_header == expected_header:
                print("CHECK 1 (Header matches): PASS")
            else:
                print(f"CHECK 1 (Header matches): FAIL. Got: {actual_header}")
        except StopIteration:
            print("CHECK 1 (Header matches): FAIL. Empty file.")
            
        rows = list(reader)
        
    # Check 2: 250 data rows
    if len(rows) == 250:
        print("CHECK 2 (250 data rows): PASS")
    else:
        print(f"CHECK 2 (250 data rows): FAIL. Got {len(rows)} rows.")
        
    # Load input requests
    with open(requests_path, "r", encoding="utf-8") as f:
        req_reader = csv.DictReader(f)
        req_dict = {r["request_id"]: r for r in req_reader}
        
    # Checks 3, 4, 5: Request IDs
    output_ids = [row[0] for row in rows]
    input_ids = list(req_dict.keys())
    
    missing_ids = set(input_ids) - set(output_ids)
    extra_ids = set(output_ids) - set(input_ids)
    duplicates = [id for id in set(output_ids) if output_ids.count(id) > 1]
    
    if missing_ids == set() and extra_ids == set() and not duplicates:
        print("CHECK 3, 4, 5 (Request IDs exact match, no missing, no dupes): PASS")
    else:
        print("CHECK 3, 4, 5 (Request IDs): FAIL.")
        if missing_ids: print(f"  Missing: {missing_ids}")
        if extra_ids: print(f"  Extra: {extra_ids}")
        if duplicates: print(f"  Duplicates: {duplicates}")
        
    # Check 6, 7, 8, 9, 10, 11
    valid_afford = {"affordable_now", "affordable_with_plan", "affordable_later", "not_affordable"}
    valid_method = {"full_payment", "partial_payment", "installments", "wait", "not_recommended"}
    
    failed_afford = []
    failed_method = []
    failed_amount = []
    failed_plan = []
    failed_spending = []
    failed_malformed = []
    
    for row in rows:
        if len(row) != 8:
            failed_malformed.append(row[0])
            continue
            
        req_id, amt_str, afford, method, plan, earliest, spending, expl = row
        
        # Check 6
        if afford not in valid_afford:
            failed_afford.append((req_id, afford))
            
        # Check 7
        if method not in valid_method:
            failed_method.append((req_id, method))
            
        # Check 8
        try:
            amt = float(amt_str)
            req_amt = float(req_dict[req_id]["requested_amount"])
            if not (0 <= amt <= req_amt):
                # allow minor float rounding
                if not (-0.01 <= amt <= req_amt + 0.01):
                    failed_amount.append((req_id, amt, req_amt))
        except ValueError:
            failed_amount.append((req_id, amt_str, "parse_error"))
            
        # Check 9: payment_plan
        if plan != "none" and plan != "":
            # Format: YYYY-MM-DD:AMOUNT|YYYY-MM-DD:AMOUNT
            if not re.match(r"^\d{4}-\d{2}-\d{2}:[0-9\.]+(\|\d{4}-\d{2}-\d{2}:[0-9\.]+)*$", plan):
                failed_plan.append((req_id, plan))
                
        # Check 10: spending_changes_needed
        if spending != "none" and spending != "":
            parts = spending.split("|")
            valid = True
            for p in parts:
                if not (p.startswith("stop:") or p.startswith("reduce_to:")):
                    valid = False
            if not valid:
                failed_spending.append((req_id, spending))
                    
    if not failed_afford:
        print("CHECK 6 (affordability_status): PASS")
    else:
        print(f"CHECK 6 (affordability_status): FAIL. Violations: {failed_afford[:5]}")
        
    if not failed_method:
        print("CHECK 7 (recommended_payment_method): PASS")
    else:
        print(f"CHECK 7 (recommended_payment_method): FAIL. Violations: {failed_method[:5]}")
        
    if not failed_amount:
        print("CHECK 8 (amount_safe_to_pay bounds): PASS")
    else:
        print(f"CHECK 8 (amount_safe_to_pay bounds): FAIL. Violations: {failed_amount[:5]}")
        
    if not failed_plan:
        print("CHECK 9 (payment_plan formatting): PASS")
    else:
        print(f"CHECK 9 (payment_plan formatting): FAIL. Violations: {failed_plan[:5]}")
        
    if not failed_spending:
        print("CHECK 10 (spending_changes formatting): PASS")
    else:
        print(f"CHECK 10 (spending_changes formatting): FAIL. Violations: {failed_spending[:5]}")
        
    if not failed_malformed:
        print("CHECK 11 (Malformed rows/unexpected columns): PASS")
    else:
        print(f"CHECK 11 (Malformed rows/unexpected columns): FAIL. Violations: {failed_malformed[:5]}")
        
    # Check 12: Usage Report
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        checks = [
            ("250 requests processed", "Number of requests processed: 250" in content),
            ("gemini-3.5-flash-lite", "gemini-3.5-flash-lite" in content),
            ("137 API calls", "Total API calls: 137" in content or "Successful calls: 137" in content),
            ("0 failed calls", "Failed calls: 0" in content),
            ("0 429", "429 count: 0" in content),
            ("0 503", "503 count: 0" in content),
            ("0 timeouts", "Timeout count: 0" in content),
            ("token usage", "Total tokens: " in content),
            ("runtime", "Runtime: " in content)
        ]
        
        all_passed = all(c[1] for c in checks)
        if all_passed:
            print("CHECK 12 (Usage report): PASS")
        else:
            print("CHECK 12 (Usage report): FAIL.")
            for name, passed in checks:
                if not passed: print(f"  Missing: {name}")
    else:
        print("CHECK 12 (Usage report): FAIL. File not found.")

if __name__ == "__main__":
    validate()
