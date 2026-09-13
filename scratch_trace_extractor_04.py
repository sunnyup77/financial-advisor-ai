import sys
sys.path.append('.')
from code.pipeline import Pipeline
from code.data_loader import DataLoader
from code.llm_extractor import EvidenceExtractor, LLMProvider

loader = DataLoader()
loader.load_all()

provider = LLMProvider("gemini-3-flash-preview")
extractor = EvidenceExtractor(provider)
pipeline = Pipeline(loader, extractor)

from code.llm_extractor import EvidenceSelector

req_id = "request_04"
req = next((r for r in loader.sample_requests if r.request_id == req_id), None)
events = [e for e in loader.events if e.user_id == req.user_id]
rel_msgs, rel_imgs = EvidenceSelector.get_relevant_evidence(req_id, req.user_id, events, loader.messages, loader.images)

print(f"Messages: {len(rel_msgs)}")
for msg in rel_msgs:
    res = extractor.extract_from_message(msg.message_id, msg.message_text, set(), {req_id}, '')
    print(f"Extracted from {msg.message_id}: {res.model_dump()}")
