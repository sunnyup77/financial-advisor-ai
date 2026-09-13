from typing import List, Dict, Tuple
from datetime import date, timedelta
import math

class Forecaster:
    def __init__(self, state, request_date: date):
        self.state = state
        self.request_date = request_date
        self.end_date = request_date + timedelta(days=90)
        self.events = state.get_forecast_events(request_date, self.end_date)
        
    def check_safety_schedule(self, schedule: List[Tuple[date, float]], spend_changes: Dict[str, float] = None) -> Tuple[bool, float]:
        """
        Simulates the 90-day cash flow with a schedule of (date, amount) payments.
        Returns (is_safe, min_headroom)
        """
        if self.state.unresolved_events:
            return False, -1.0
            
        spend_changes = spend_changes or {}
        
        current_bal = self.state.current_balance
        min_headroom = current_bal - self.state.minimum_balance
        
        events_by_date = {}
        for ev in self.events:
            d = ev["date"]
            if d not in events_by_date:
                events_by_date[d] = []
            events_by_date[d].append(ev)
            
        payments_by_date = {}
        for d, amt in schedule:
            if d not in payments_by_date:
                payments_by_date[d] = 0.0
            payments_by_date[d] += amt
            
        reduce_cats = set(self.state.profile.expense_categories_user_is_willing_to_reduce) if self.state.profile.expense_categories_user_is_willing_to_reduce else set()
        stop_cats = set(self.state.profile.expense_categories_user_is_willing_to_stop) if self.state.profile.expense_categories_user_is_willing_to_stop else set()
        
        curr_date = self.request_date
        while curr_date <= self.end_date:
            if curr_date in events_by_date:
                for ev in events_by_date[curr_date]:
                    amt = ev["amount"]
                    if ev["event_id"] in spend_changes:
                        if ev["category"] in reduce_cats and ev["flexibility"] == "reducible":
                            amt = -spend_changes[ev["event_id"]]
                        elif ev["category"] in stop_cats and ev["flexibility"] == "stoppable":
                            if spend_changes[ev["event_id"]] == 0:
                                amt = 0
                    current_bal += amt
                    
            if curr_date in payments_by_date:
                current_bal -= payments_by_date[curr_date]
                    
            headroom = current_bal - self.state.minimum_balance
            if headroom < min_headroom:
                min_headroom = headroom
                
            curr_date += timedelta(days=1)
            
        return (min_headroom >= 0), min_headroom

    def check_safety(self, initial_deduction: float, spend_changes: Dict[str, float] = None) -> Tuple[bool, float]:
        return self.check_safety_schedule([(self.request_date, initial_deduction)], spend_changes)

    def calculate_amount_safe_to_pay(self, requested_amount: float) -> float:
        if self.state.unresolved_events:
            return 0.0
            
        is_safe, min_headroom = self.check_safety(0.0)
        if min_headroom < 0:
            return 0.0
            
        return max(0.0, min(requested_amount, min_headroom))

    def calculate_earliest_full_payment(self, requested_amount: float) -> str:
        """
        Finds earliest date where deducting requested_amount preserves minimum balance
        for the *remaining* forecast horizon.
        """
        if self.state.unresolved_events:
            return ""
            
        current_bal = self.state.current_balance
        daily_balances = {}
        
        events_by_date = {}
        for ev in self.events:
            d = ev["date"]
            if d not in events_by_date:
                events_by_date[d] = []
            events_by_date[d].append(ev)
            
        curr_date = self.request_date
        min_balance = self.state.minimum_balance
        
        # Calculate base balance
        while curr_date <= self.end_date:
            if curr_date in events_by_date:
                for ev in events_by_date[curr_date]:
                    current_bal += ev["amount"]
            daily_balances[curr_date] = current_bal
            if current_bal < min_balance:
                return "" # Baseline is unsafe, can't afford anything
            curr_date += timedelta(days=1)
            
        for d_offset in range(91):
            test_date = self.request_date + timedelta(days=d_offset)
            safe = True
            
            for t_offset in range(d_offset, 91):
                t_date = self.request_date + timedelta(days=t_offset)
                if daily_balances[t_date] - requested_amount < min_balance:
                    safe = False
                    break
                    
            if safe:
                return test_date.isoformat()
                
        return ""
