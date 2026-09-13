from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List
import datetime

def parse_date(d_str: str) -> Optional[date]:
    if not d_str:
        return None
    return datetime.datetime.strptime(d_str.strip(), "%Y-%m-%d").date()

def parse_float(f_str: str) -> Optional[float]:
    if not f_str:
        return None
    return float(f_str.strip())

def parse_bool(b_str: str) -> bool:
    return b_str.strip().lower() == "true"

def parse_list(l_str: str) -> List[str]:
    if not l_str:
        return []
    return [s.strip() for s in l_str.split('|')]

@dataclass
class RequestData:
    request_id: str
    user_id: str
    request_date: date
    request_type: str
    requested_amount: float
    desired_completion_date: date
    allows_partial_payment: bool
    request_text: str

    def __post_init__(self):
        if isinstance(self.request_date, str):
            self.request_date = parse_date(self.request_date)
        if isinstance(self.requested_amount, str):
            self.requested_amount = parse_float(self.requested_amount)
        if isinstance(self.desired_completion_date, str):
            self.desired_completion_date = parse_date(self.desired_completion_date)
        if isinstance(self.allows_partial_payment, str):
            self.allows_partial_payment = parse_bool(self.allows_partial_payment)

@dataclass
class FinancialProfile:
    user_id: str
    home_currency: str
    current_available_balance: float
    minimum_balance_to_keep: float
    financial_priorities: List[str]
    expense_categories_to_protect: List[str]
    expense_categories_user_is_willing_to_reduce: List[str]
    expense_categories_user_is_willing_to_stop: List[str]
    payment_methods_user_will_consider: List[str]
    max_installment_months: Optional[int]

    def __post_init__(self):
        if isinstance(self.current_available_balance, str):
            self.current_available_balance = parse_float(self.current_available_balance)
        if isinstance(self.minimum_balance_to_keep, str):
            self.minimum_balance_to_keep = parse_float(self.minimum_balance_to_keep)
        if isinstance(self.financial_priorities, str):
            self.financial_priorities = parse_list(self.financial_priorities)
        if isinstance(self.expense_categories_to_protect, str):
            self.expense_categories_to_protect = parse_list(self.expense_categories_to_protect)
        if isinstance(self.expense_categories_user_is_willing_to_reduce, str):
            self.expense_categories_user_is_willing_to_reduce = parse_list(self.expense_categories_user_is_willing_to_reduce)
        if isinstance(self.expense_categories_user_is_willing_to_stop, str):
            self.expense_categories_user_is_willing_to_stop = parse_list(self.expense_categories_user_is_willing_to_stop)
        if isinstance(self.payment_methods_user_will_consider, str):
            self.payment_methods_user_will_consider = parse_list(self.payment_methods_user_will_consider)
        if isinstance(self.max_installment_months, str):
            self.max_installment_months = int(self.max_installment_months) if self.max_installment_months.strip() else None

@dataclass
class FinancialEvent:
    event_id: str
    user_id: str
    event_type: str
    description: str
    category: str
    direction: str
    amount: Optional[float]
    currency: str
    event_date: date
    settlement_date: Optional[date]
    status: str
    linked_event_id: str
    flexibility: str
    minimum_allowed_amount: Optional[float]

    def __post_init__(self):
        if isinstance(self.amount, str):
            self.amount = parse_float(self.amount) if self.amount.strip() else None
        if isinstance(self.event_date, str):
            self.event_date = parse_date(self.event_date)
        if isinstance(self.settlement_date, str):
            self.settlement_date = parse_date(self.settlement_date) if self.settlement_date.strip() else None
        if isinstance(self.minimum_allowed_amount, str):
            self.minimum_allowed_amount = parse_float(self.minimum_allowed_amount) if self.minimum_allowed_amount.strip() else None

@dataclass
class ExchangeRate:
    rate_date: date
    from_currency: str
    to_currency: str
    rate: float

    def __post_init__(self):
        if isinstance(self.rate_date, str):
            self.rate_date = parse_date(self.rate_date)
        if isinstance(self.rate, str):
            self.rate = parse_float(self.rate)

@dataclass
class PaymentOption:
    payment_option_id: str
    request_id: str
    payment_method: str
    payment_amount: float
    number_of_payments: int
    first_payment_date: date
    payment_frequency_days: Optional[int]
    financing_fee: float
    total_payable_amount: float

    def __post_init__(self):
        if isinstance(self.payment_amount, str):
            self.payment_amount = parse_float(self.payment_amount)
        if isinstance(self.number_of_payments, str):
            self.number_of_payments = int(self.number_of_payments)
        if isinstance(self.first_payment_date, str):
            self.first_payment_date = parse_date(self.first_payment_date)
        if isinstance(self.payment_frequency_days, str):
            self.payment_frequency_days = int(self.payment_frequency_days) if self.payment_frequency_days.strip() else None
        if isinstance(self.financing_fee, str):
            self.financing_fee = parse_float(self.financing_fee)
        if isinstance(self.total_payable_amount, str):
            self.total_payable_amount = parse_float(self.total_payable_amount)

@dataclass
class Message:
    message_id: str
    user_id: str
    request_id: str
    related_event_id: str
    sent_at: str
    source_type: str
    message_text: str

@dataclass
class ImageInfo:
    image_id: str
    user_id: str
    request_id: str
    related_event_id: str
