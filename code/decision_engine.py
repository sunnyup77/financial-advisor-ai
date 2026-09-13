import itertools
from typing import List, Dict, Tuple, Optional
from datetime import date, timedelta
from dataclasses import dataclass, field

from code.models import RequestData, FinancialProfile, PaymentOption
from code.financial_state import FinancialState
from code.forecast import Forecaster

@dataclass
class CandidatePlan:
    method: str
    schedule: List[Tuple[date, float]]
    payment_option_id: Optional[str] = None
    spend_changes: Dict[str, float] = field(default_factory=dict)
    is_safe: bool = False
    min_headroom: float = 0.0
    
    total_amount_paid: float = field(init=False)
    first_payment_date: Optional[date] = field(init=False)
    num_payments: int = field(init=False)
    
    def __post_init__(self):
        self.total_amount_paid = sum(amt for _, amt in self.schedule)
        self.first_payment_date = min((d for d, _ in self.schedule), default=None)
        self.num_payments = len(self.schedule)

@dataclass
class DecisionResult:
    request_id: str
    amount_safe_to_pay: float
    affordability_status: str
    recommended_payment_method: str
    payment_plan: str
    earliest_date_for_full_payment: str
    spending_changes_needed: str
    decision_explanation: str

def format_payment_plan(schedule: List[Tuple[date, float]]) -> str:
    if not schedule:
        return "none"
    parts = []
    for d, amt in sorted(schedule, key=lambda x: x[0]):
        amt_str = f"{amt:.2f}".rstrip('0').rstrip('.')
        parts.append(f"{d.isoformat()}:{amt_str}")
    return "|".join(parts)

def format_spending_changes(changes: Dict[str, float]) -> str:
    if not changes:
        return "none"
    parts = []
    for ev_id, amt in changes.items():
        if amt == 0:
            parts.append(f"stop:{ev_id}")
        else:
            amt_str = f"{amt:.2f}".rstrip('0').rstrip('.')
            parts.append(f"reduce_to:{ev_id}:{amt_str}")
    return "|".join(sorted(parts))

class DecisionEngine:
    def __init__(self, request: RequestData, state: FinancialState, forecaster: Forecaster, options: List[PaymentOption]):
        self.request = request
        self.state = state
        self.forecaster = forecaster
        self.options = [o for o in options if o.request_id == request.request_id]
        
        self.amount_safe_to_pay = forecaster.calculate_amount_safe_to_pay(request.requested_amount)
        self.earliest_date_for_full_payment_str = forecaster.calculate_earliest_full_payment(request.requested_amount)
        if self.earliest_date_for_full_payment_str:
            self.earliest_date_for_full_payment = date.fromisoformat(self.earliest_date_for_full_payment_str)
        else:
            self.earliest_date_for_full_payment = None

    def _get_flexible_changes(self) -> List[Dict[str, float]]:
        flexible_events = []
        reduce_cats = set(self.state.profile.expense_categories_user_is_willing_to_reduce) if self.state.profile.expense_categories_user_is_willing_to_reduce else set()
        stop_cats = set(self.state.profile.expense_categories_user_is_willing_to_stop) if self.state.profile.expense_categories_user_is_willing_to_stop else set()
        
        for ev in self.forecaster.events:
            if ev["amount"] < 0:
                is_reducible = ev["category"] in reduce_cats and ev["flexibility"] == "reducible"
                is_stoppable = ev["category"] in stop_cats and ev["flexibility"] == "stoppable"
                if is_reducible or is_stoppable:
                    flexible_events.append(ev)
                    
        possible_changes = []
        for ev in flexible_events:
            if ev["category"] in reduce_cats and ev["flexibility"] == "reducible":
                possible_changes.append((ev["event_id"], ev["minimum_allowed_amount"] or 0.0))
            elif ev["category"] in stop_cats and ev["flexibility"] == "stoppable":
                possible_changes.append((ev["event_id"], 0.0))
                
        unique_changes = {c[0]: c[1] for c in possible_changes}
        change_items = list(unique_changes.items())
        
        combos = []
        for r in range(1, min(4, len(change_items) + 1)):
            for comb in itertools.combinations(change_items, r):
                combos.append(dict(comb))
        return combos

    def generate_base_candidates(self) -> List[CandidatePlan]:
        candidates = []
        allowed_methods = set(self.state.profile.payment_methods_user_will_consider)
        req_amt = self.request.requested_amount
        req_date = self.request.request_date
        
        if "full_payment" in allowed_methods:
            candidates.append(CandidatePlan("full_payment", [(req_date, req_amt)]))
            
        if "partial_payment" in allowed_methods and self.request.allows_partial_payment:
            if 0 < self.amount_safe_to_pay < req_amt:
                if self.earliest_date_for_full_payment and self.earliest_date_for_full_payment <= self.request.desired_completion_date:
                    rem = req_amt - self.amount_safe_to_pay
                    candidates.append(CandidatePlan("partial_payment", [(req_date, self.amount_safe_to_pay), (self.earliest_date_for_full_payment, rem)]))
                    
        if "wait" in allowed_methods:
            if self.earliest_date_for_full_payment and self.earliest_date_for_full_payment <= self.request.desired_completion_date:
                candidates.append(CandidatePlan("wait", [(self.earliest_date_for_full_payment, req_amt)]))
                
        if "installments" in allowed_methods:
            for opt in self.options:
                end_date = opt.first_payment_date
                if opt.number_of_payments > 1:
                    end_date += timedelta(days=(opt.number_of_payments - 1) * (opt.payment_frequency_days or 0))
                    
                if end_date <= self.request.desired_completion_date:
                    schedule = []
                    for i in range(opt.number_of_payments):
                        d = opt.first_payment_date + timedelta(days=i * (opt.payment_frequency_days or 0))
                        schedule.append((d, opt.payment_amount))
                    candidates.append(CandidatePlan("installments", schedule, payment_option_id=opt.payment_option_id))
                    
        return candidates

    def process_candidates(self) -> List[CandidatePlan]:
        base_candidates = self.generate_base_candidates()
        valid_candidates = []
        spend_combos = self._get_flexible_changes()
        
        for cand in base_candidates:
            is_safe, min_headroom = self.forecaster.check_safety_schedule(cand.schedule)
            if is_safe:
                cand.is_safe = True
                cand.min_headroom = min_headroom
                valid_candidates.append(cand)
            else:
                for combo in spend_combos:
                    is_safe, min_headroom = self.forecaster.check_safety_schedule(cand.schedule, combo)
                    if is_safe:
                        cand_with_changes = CandidatePlan(
                            method=cand.method,
                            schedule=cand.schedule,
                            payment_option_id=cand.payment_option_id,
                            spend_changes=combo,
                        )
                        cand_with_changes.is_safe = True
                        cand_with_changes.min_headroom = min_headroom
                        valid_candidates.append(cand_with_changes)
                        
        return valid_candidates

    def rank_candidates(self, candidates: List[CandidatePlan]) -> Optional[CandidatePlan]:
        if not candidates:
            return None
            
        def rank_key(c: CandidatePlan):
            return (
                0, # complete by desired date (prefiltered)
                0 if len(c.spend_changes) == 0 else 1, # prefer no spending changes
                c.total_amount_paid, # minimize total amount
                c.first_payment_date.toordinal() if c.first_payment_date else float('inf'), # start earlier
                c.num_payments, # fewer payments
                c.payment_option_id or "", # lowest payment option id
            )
            
        return min(candidates, key=rank_key)

    def generate_explanation(self, best: CandidatePlan, status: str) -> str:
        if not best:
            return "No safe payment plan could be found matching your preferences without violating the minimum balance."
            
        cur = self.state.profile.home_currency
        headroom = f"{best.min_headroom:,.2f}".rstrip('0').rstrip('.')
        
        if best.method == "full_payment":
            amt = f"{self.request.requested_amount:,.2f}".rstrip('0').rstrip('.')
            exp = f"Pay {cur} {amt} today. This leaves at least {cur} {headroom} available over the next 90 days."
        elif best.method == "installments":
            opt = next((o for o in self.options if o.payment_option_id == best.payment_option_id), None)
            amt = f"{opt.payment_amount:,.2f}".rstrip('0').rstrip('.') if opt else "0"
            date_str = best.first_payment_date.strftime("%d %B %Y").lstrip('0')
            exp = f"Use {best.num_payments} installments of {cur} {amt}, starting {date_str}. This leaves at least {cur} {headroom} available."
        elif best.method == "wait":
            amt = f"{self.request.requested_amount:,.2f}".rstrip('0').rstrip('.')
            date_str = best.first_payment_date.strftime("%d %B %Y").lstrip('0')
            exp = f"Wait until {date_str} to pay the full {cur} {amt}. This leaves at least {cur} {headroom} available."
        elif best.method == "partial_payment":
            p1 = f"{best.schedule[0][1]:,.2f}".rstrip('0').rstrip('.')
            p2 = f"{best.schedule[1][1]:,.2f}".rstrip('0').rstrip('.')
            date_str = best.schedule[1][0].strftime("%d %B %Y").lstrip('0')
            exp = f"Make a partial payment of {cur} {p1} today, and the remaining {cur} {p2} on {date_str}. This leaves at least {cur} {headroom} available."
        else:
            exp = "Payment plan approved."
            
        if best.spend_changes:
            exp += f" This requires {len(best.spend_changes)} spending changes."
            
        return exp

    def build_decision(self) -> DecisionResult:
        valid_candidates = self.process_candidates()
        best_candidate = self.rank_candidates(valid_candidates)
        
        if not best_candidate:
            status = "not_affordable"
            method = "not_recommended"
            plan_str = "none"
            spend_str = "none"
            exp = self.generate_explanation(None, status)
        else:
            method = best_candidate.method
            if self.amount_safe_to_pay == self.request.requested_amount:
                status = "affordable_now"
            elif self.earliest_date_for_full_payment and self.earliest_date_for_full_payment <= self.request.desired_completion_date:
                status = "affordable_later"
            else:
                status = "affordable_with_plan"
                
            plan_str = format_payment_plan(best_candidate.schedule)
            spend_str = format_spending_changes(best_candidate.spend_changes)
            exp = self.generate_explanation(best_candidate, status)
            
        # Amount formatting for output
        amt_safe_str = f"{self.amount_safe_to_pay:.2f}".rstrip('0').rstrip('.') if self.amount_safe_to_pay > 0 else "0"
        if amt_safe_str == "": amt_safe_str = "0"
            
        return DecisionResult(
            request_id=self.request.request_id,
            amount_safe_to_pay=amt_safe_str,
            affordability_status=status,
            recommended_payment_method=method,
            payment_plan=plan_str,
            earliest_date_for_full_payment=self.earliest_date_for_full_payment_str or "none",
            spending_changes_needed=spend_str,
            decision_explanation=exp
        )
