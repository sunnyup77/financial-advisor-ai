import sys
import os
import csv
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

sys.path.append('.')

from code.models import RequestData
from code.data_loader import DataLoader
from code.pipeline import Pipeline
from code.llm_extractor import EvidenceExtractor, EvidenceSelector
from code.financial_state import FinancialState
from code.forecast import Forecaster
from code.decision_engine import DecisionEngine

# Load datasets
loader = DataLoader()
loader.load_all()

class MockProvider:
    def generate_json(self, *args, **kwargs):
        return {"extracted_facts": []}
        
extractor = EvidenceExtractor(provider=MockProvider())
pipeline = Pipeline(loader, extractor)

def trace_request(req_id):
    print(f"\n{'='*50}")
    print(f"TRACING {req_id}")
    print(f"{'='*50}")
    
    # 1. Load request
    req = next((r for r in loader.sample_requests if r.request_id == req_id), None)
    if not req:
        print("Request not found.")
        return
    
    print(f"Request Amount: {req.requested_amount}")
    print(f"Request Date: {req.request_date}")
    print(f"Desired Date: {req.desired_completion_date}")
    
    # Get profile and events
    profile = next((p for p in loader.profiles if p.user_id == req.user_id), None)
    pipeline.converter.home_currency = profile.home_currency
    events = [e for e in loader.events if e.user_id == req.user_id]
    
    # Evidence Selection
    rel_msgs, rel_imgs = EvidenceSelector.get_relevant_evidence(
        req.request_id, req.user_id, events, loader.messages, loader.images
    )
    
    print(f"Found {len(rel_msgs)} messages and {len(rel_imgs)} images")
    
    # We will just pass empty facts to test if deterministic engine differs!
    # Wait, the cache is active because extractor uses it!
    # The MockProvider will return [] if cache misses, but we just ran it, so cache will hit!
    facts = []
    valid_event_ids = set([e.event_id for e in events])
    valid_request_ids = {req.request_id}
    
    for msg in rel_msgs:
        res = extractor.extract_from_message(msg.message_id, msg.message_text, valid_event_ids, valid_request_ids, msg.related_event_id or '')
        facts.extend(res.facts)
    for img in rel_imgs:
        res = extractor.extract_from_image(img.image_id, "", valid_event_ids, valid_request_ids, img.related_event_id or '')
        facts.extend(res.facts)
        
    print(f"Extracted Facts: {[f.model_dump() for f in facts]}")
    
    # Financial State
    state = FinancialState(profile, events, pipeline.converter)
    state.apply_facts(facts)
    
    print(f"\n--- STATE ---")
    print(f"Starting Balance: {state.current_balance}")
    print(f"Min Balance: {state.minimum_balance}")
    
    # Forecast
    forecaster = Forecaster(state, req.request_date)
    print(f"\n--- FORECAST ---")
    print(f"Forecasted events:")
    for ev in sorted(forecaster.events, key=lambda x: x["date"]):
        if req.request_date <= ev["date"] <= (req.request_date + timedelta(days=15)):
            print(f"  {ev['date']}: {ev['amount']} ({ev['event_id']})")
            
    is_safe, min_headroom = forecaster.check_safety(0.0)
    print(f"Minimum Headroom over 90 days: {min_headroom}")
    
    # Decision Engine
    engine = DecisionEngine(req, state, forecaster, loader.payment_options)
    print(f"Allowed Methods: {engine.state.profile.payment_methods_user_will_consider}")
    print(f"Earliest Full Date: {engine.earliest_date_for_full_payment_str}")
    
    print("\n--- BASE CANDIDATES ---")
    base_cands = engine.generate_base_candidates()
    for c in base_cands:
        print(f"Cand {c.method}: {c.schedule}")
        
    print("\n--- CANDIDATES ---")
    valid_cands = engine.process_candidates()
    for c in valid_cands:
        rk = (
            0,
            0 if len(c.spend_changes) == 0 else 1,
            c.total_amount_paid,
            c.first_payment_date.toordinal() if c.first_payment_date else float('inf'),
            c.num_payments,
            c.payment_option_id or ""
        )
        print(f"Cand {c.method}: {c.schedule} | changes: {c.spend_changes} | safe: {c.is_safe} | key: {rk}")
    
    result = engine.build_decision()
    
    print(f"\n--- DECISION ---")
    print(f"Status: {result.affordability_status}")
    print(f"Safe Amount: {result.amount_safe_to_pay}")
    print(f"Recommended Method: {result.recommended_payment_method}")
    print(f"Payment Plan: {result.payment_plan}")
    print(f"Spending Changes: {result.spending_changes_needed}")
    print(f"Explanation: {result.decision_explanation}")
    
trace_request("request_04")
trace_request("request_12")
