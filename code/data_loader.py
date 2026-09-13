import csv
from typing import List, Dict
from code.config import (
    REQUESTS_CSV, SAMPLE_REQUESTS_CSV, PROFILES_CSV, EVENTS_CSV,
    EXCHANGE_RATES_CSV, PAYMENT_OPTIONS_CSV, MESSAGES_CSV, IMAGES_CSV
)
from code.models import (
    RequestData, FinancialProfile, FinancialEvent, ExchangeRate,
    PaymentOption, Message, ImageInfo
)

def _load_csv(filepath: str) -> List[Dict[str, str]]:
    data = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

class DataLoader:
    def __init__(self):
        self.requests: List[RequestData] = []
        self.sample_requests: List[RequestData] = []
        self.profiles: List[FinancialProfile] = []
        self.events: List[FinancialEvent] = []
        self.rates: List[ExchangeRate] = []
        self.payment_options: List[PaymentOption] = []
        self.messages: List[Message] = []
        self.images: List[ImageInfo] = []

    def load_all(self):
        self.requests = [RequestData(**row) for row in _load_csv(REQUESTS_CSV)]
        self.sample_requests = [
            RequestData(
                request_id=row['request_id'],
                user_id=row['user_id'],
                request_date=row['request_date'],
                request_type=row['request_type'],
                requested_amount=row['requested_amount'],
                desired_completion_date=row['desired_completion_date'],
                allows_partial_payment=row['allows_partial_payment'],
                request_text=row['request_text']
            ) for row in _load_csv(SAMPLE_REQUESTS_CSV)
        ]
        self.profiles = [FinancialProfile(**row) for row in _load_csv(PROFILES_CSV)]
        self.events = [FinancialEvent(**row) for row in _load_csv(EVENTS_CSV)]
        self.rates = [ExchangeRate(**row) for row in _load_csv(EXCHANGE_RATES_CSV)]
        self.payment_options = [PaymentOption(**row) for row in _load_csv(PAYMENT_OPTIONS_CSV)]
        self.messages = [Message(**row) for row in _load_csv(MESSAGES_CSV)]
        self.images = [ImageInfo(**row) for row in _load_csv(IMAGES_CSV)]

    def validate_relationships(self) -> List[str]:
        errors = []
        # Check if users in requests exist in profiles
        profile_users = {p.user_id for p in self.profiles}
        for req in self.requests:
            if req.user_id not in profile_users:
                errors.append(f"Request {req.request_id} has unknown user_id {req.user_id}")

        # Check if requests in payment_options exist
        request_ids = {r.request_id for r in self.requests} | {r.request_id for r in self.sample_requests}
        for opt in self.payment_options:
            if opt.request_id not in request_ids:
                errors.append(f"PaymentOption {opt.payment_option_id} has unknown request_id {opt.request_id}")

        # Check if events user_ids are in profiles
        for ev in self.events:
            if ev.user_id not in profile_users:
                errors.append(f"Event {ev.event_id} has unknown user_id {ev.user_id}")

        return errors
