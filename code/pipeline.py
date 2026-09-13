from typing import List, Dict
from code.models import RequestData
from code.data_loader import DataLoader
from code.currency import CurrencyConverter
from code.llm_extractor import EvidenceExtractor, LLMProvider
from code.financial_state import FinancialState
from code.forecast import Forecaster
from code.decision_engine import DecisionEngine, DecisionResult

class Pipeline:
    def __init__(self, data_loader: DataLoader, extractor: EvidenceExtractor):
        self.data = data_loader
        self.extractor = extractor
        self.converter = CurrencyConverter(self.data.rates, "")
        
    def process_request(self, request: RequestData) -> DecisionResult:
        profile = next((p for p in self.data.profiles if p.user_id == request.user_id), None)
        if not profile:
            raise ValueError(f"Profile not found for user {request.user_id}")
            
        self.converter.home_currency = profile.home_currency
        
        events = [e for e in self.data.events if e.user_id == request.user_id]
        
        from code.llm_extractor import EvidenceSelector
        
        # 1. Extract facts (using Phase 2 isolated logic)
        facts = []
        valid_event_ids = set([e.event_id for e in events])
        valid_request_ids = {request.request_id}
        
        rel_msgs, rel_imgs = EvidenceSelector.get_relevant_evidence(
            request.request_id, request.user_id, events, self.data.messages, self.data.images
        )
        
        for msg in rel_msgs:
            res = self.extractor.extract_from_message(msg.message_id, msg.message_text, valid_event_ids, valid_request_ids, msg.related_event_id or '')
            if res.error:
                print(f"Extraction error for msg {msg.message_id}: {res.error}")
            facts.extend(res.facts)
            
        for img in rel_imgs:
            import os
            image_path = os.path.join("INFO", "dataset", "images", f"{img.image_id}.png")
            res = self.extractor.extract_from_image(img.image_id, image_path, valid_event_ids, valid_request_ids, img.related_event_id or '')
            if res.error:
                print(f"Extraction error for img {img.image_id}: {res.error}")
            facts.extend(res.facts)
        
        # 2. Reconstruct Financial State
        state = FinancialState(profile, events, self.converter)
        state.apply_facts(facts)
        
        # 3. Simulate 90-day Forecast
        forecaster = Forecaster(state, request.request_date)
        
        # 4. Generate Decision
        engine = DecisionEngine(request, state, forecaster, self.data.payment_options)
        return engine.build_decision()
