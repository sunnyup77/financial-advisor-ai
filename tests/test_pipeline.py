import unittest
import os
import json
import shutil
from datetime import date
from code.models import RequestData, FinancialProfile, FinancialEvent, Message, ImageInfo
from code.data_loader import DataLoader
from code.llm_extractor import EvidenceExtractor, LLMProvider, EvidenceSelector, ExtractedFact

class MockProvider(LLMProvider):
    def __init__(self):
        self.calls = 0

    def generate_json(self, prompt: str, image_path: str = None) -> str:
        self.calls += 1
        # Mocking a valid JSON response from Gemini
        return '{"extracted_facts": [{"fact_type": "update_amount", "confidence": "high", "requires_deterministic_validation": true, "new_amount": 999.0}]}'
        
    def get_usage(self) -> dict:
        return {"input_tokens": 10, "output_tokens": 10, "total_tokens": 20, "estimated_cost_usd": 0.001}

class TestEvidenceSelection(unittest.TestCase):
    def test_evidence_selection_rules(self):
        user_id = "u1"
        request_id = "req1"
        
        # Events (event_id, user_id, event_type, description, category, direction, amount, currency, event_date, settlement_date, status, linked_event_id, flexibility, min_amount)
        e1_missing = FinancialEvent("e1", user_id, "type", "desc", "cat", "credit", None, "USD", date(2024, 1, 1), None, "pending", "", "fixed", None)
        e2_has_amt = FinancialEvent("e2", user_id, "type", "desc", "cat", "debit", 100.0, "USD", date(2024, 1, 2), None, "settled", "", "fixed", None)
        e3_other_usr = FinancialEvent("e3", "u2", "type", "desc", "cat", "debit", None, "USD", date(2024, 1, 3), None, "pending", "", "fixed", None)
        
        user_events = [e1_missing, e2_has_amt]
        
        # Messages (message_id, user_id, request_id, related_event_id, sent_at, source_type, message_text)
        m1_req = Message("m1", user_id, "req1", "", "2024-01-01", "email", "message about req1")
        m2_rel = Message("m2", user_id, "", "e2", "2024-01-01", "email", "message about e2")
        m3_irrel = Message("m3", user_id, "req99", "e99", "2024-01-01", "email", "irrelevant to current req or events")
        m4_other = Message("m4", "u2", "req1", "", "2024-01-01", "email", "other user message")
        
        all_messages = [m1_req, m2_rel, m3_irrel, m4_other]
        
        # Images
        i1_req = ImageInfo("i1", user_id, "req1", "") # current request image
        i2_missing = ImageInfo("i2", user_id, "", "e1") # related to event missing amount
        i3_has_amt = ImageInfo("i3", user_id, "", "e2") # related to event that already has amount (not missing, should be excluded based on phase 2 rules! wait, phase 2 rule says prioritize images linked to events missing amounts. Actually EvidenceSelector code: "if img.related_event_id in events_missing_amounts: relevant_images.append(img); elif img.request_id == request_id: relevant_images.append(img)" -> so i3_has_amt is EXCLUDED!)
        i4_irrel = ImageInfo("i4", user_id, "req99", "e99")
        i5_other = ImageInfo("i5", "u2", "req1", "")
        
        all_images = [i1_req, i2_missing, i3_has_amt, i4_irrel, i5_other]
        
        rel_msgs, rel_imgs = EvidenceSelector.get_relevant_evidence(request_id, user_id, user_events, all_messages, all_images)
        
        # Assert messages
        msg_ids = [m.message_id for m in rel_msgs]
        self.assertIn("m1", msg_ids) # current request
        self.assertIn("m2", msg_ids) # related event
        self.assertNotIn("m3", msg_ids) # irrelevant
        self.assertNotIn("m4", msg_ids) # wrong user
        
        # Assert images
        img_ids = [i.image_id for i in rel_imgs]
        self.assertIn("i1", img_ids) # current request
        self.assertIn("i2", img_ids) # missing amount event
        self.assertNotIn("i3", img_ids) # related event but already has amount -> excluded!
        self.assertNotIn("i4", img_ids) # irrelevant
        self.assertNotIn("i5", img_ids) # wrong user

class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.cache_dir = ".test_cache"
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            
    def tearDown(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            
    def test_pipeline_smoke_and_cache(self):
        loader = DataLoader()
        # Mock minimal data
        loader.profiles = [FinancialProfile("u1", "USD", 1000.0, 200.0, "", "", "", "", "full_payment", "")]
        loader.events = []
        loader.rates = []
        loader.payment_options = []
        loader.messages = [Message("m1", "u1", "r1", "", "2024-01-01", "email", "text")]
        loader.images = []
        
        request = RequestData("r1", "u1", date(2024, 1, 1), "purchase", 500.0, date(2024, 1, 20), True, "")
        
        provider = MockProvider()
        extractor = EvidenceExtractor(provider, cache_dir=self.cache_dir)
        
        # Call 1: Misses cache, uses provider
        res1 = extractor.extract_from_message("m1", "text", set(), {"r1"}, "")
        self.assertEqual(provider.calls, 1)
        self.assertEqual(len(res1.facts), 1)
        self.assertEqual(res1.facts[0].new_amount, 999.0)
        
        # Call 2: Hits cache, provider not called
        res2 = extractor.extract_from_message("m1", "text", set(), {"r1"}, "")
        self.assertEqual(provider.calls, 1) # Still 1! Cache works.
        self.assertEqual(len(res2.facts), 1)
        
        # Ensure pipeline works
        from code.pipeline import Pipeline
        pipeline = Pipeline(loader, extractor)
        result = pipeline.process_request(request)
        self.assertEqual(result.request_id, "r1")

if __name__ == '__main__':
    unittest.main()
