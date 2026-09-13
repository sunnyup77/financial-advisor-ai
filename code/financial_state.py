from typing import List, Dict, Tuple
from datetime import date, timedelta
from collections import defaultdict
import math

from code.models import FinancialProfile, FinancialEvent
from code.currency import CurrencyConverter
from code.llm_extractor import ExtractedFact

class FinancialState:
    def __init__(self, profile: FinancialProfile, events: List[FinancialEvent], converter: CurrencyConverter):
        self.profile = profile
        self.events = events
        self.converter = converter
        self.current_balance = profile.current_available_balance
        self.minimum_balance = profile.minimum_balance_to_keep
        
        self.unresolved_events = set()

    def apply_facts(self, facts: List[ExtractedFact]):
        fact_map = {f.affected_event_id: f for f in facts if f.affected_event_id}
        for ev in self.events:
            if ev.event_id in fact_map:
                f = fact_map[ev.event_id]
                if f.fact_type == "update_amount" and f.new_amount is not None:
                    ev.amount = f.new_amount
                elif f.fact_type == "update_date" and f.new_date is not None:
                    try:
                        ev.event_date = date.fromisoformat(f.new_date)
                    except ValueError:
                        pass
                elif f.fact_type == "cancel_event":
                    ev.status = "cancelled"

    def _infer_recurrence(self) -> Dict[Tuple[str, str, str, str, str], dict]:
        """
        Infers recurrence conservatively from dataset history.
        Uses 3-occurrence threshold and strict median interval matching.
        """
        groups = defaultdict(list)
        for ev in self.events:
            if ev.status == 'settled' and ev.amount is not None:
                groups[(ev.user_id, ev.category, ev.description, ev.direction, ev.currency)].append(ev)
                
        recurring = {}
        for key, group_events in groups.items():
            if len(group_events) >= 3:
                sorted_events = sorted(group_events, key=lambda e: e.event_date)
                intervals = []
                for i in range(1, len(sorted_events)):
                    diff = (sorted_events[i].event_date - sorted_events[i-1].event_date).days
                    intervals.append(diff)
                    
                intervals.sort()
                mid = len(intervals) // 2
                median_interval = intervals[mid] if len(intervals) % 2 != 0 else (intervals[mid-1] + intervals[mid]) / 2.0
                
                # Check tight bounds
                if 6 <= median_interval <= 8:
                    freq = timedelta(days=7)
                elif 13 <= median_interval <= 15:
                    freq = timedelta(days=14)
                elif 27 <= median_interval <= 32:
                    freq = timedelta(days=round(median_interval))
                else:
                    continue
                    
                amounts = [e.amount for e in sorted_events]
                if key[3] == 'debit':
                    proj_amt = max(amounts)
                else:
                    proj_amt = min(amounts)
                    
                recurring[key] = {
                    "interval": freq,
                    "projected_amount": proj_amt,
                    "latest_date": sorted_events[-1].event_date,
                    "flexibility": sorted_events[-1].flexibility,
                    "event_type": sorted_events[-1].event_type,
                    "minimum_allowed_amount": sorted_events[-1].minimum_allowed_amount
                }
        return recurring

    def get_forecast_events(self, start_date: date, end_date: date) -> List[Dict]:
        forecast = []
        processed_links = set()
        self.unresolved_events.clear()
        
        latest_explicit = {}
        
        for ev in sorted(self.events, key=lambda e: e.event_date):
            if ev.status in ["failed", "cancelled", "duplicate", "unrealized"]:
                continue
                
            if ev.status == "pending" and ev.direction == "credit":
                continue 
                
            if ev.linked_event_id:
                if ev.linked_event_id in processed_links:
                    continue
                processed_links.add(ev.linked_event_id)
            processed_links.add(ev.event_id)
            
            effective_date = ev.settlement_date if ev.settlement_date else ev.event_date
            key = (ev.user_id, ev.category, ev.description, ev.direction, ev.currency)
            
            if ev.status == "settled" and effective_date < start_date:
                # Still track the latest explicit date for recurrence prevention
                if key not in latest_explicit or effective_date > latest_explicit[key]:
                    latest_explicit[key] = effective_date
                    
                # If a settled event that is part of a recurring group has an unknown amount,
                # we can't reliably project the series.
                if ev.amount is None:
                    self.unresolved_events.add(ev.event_id)
                continue
                
            if ev.amount is None:
                if ev.status in ["pending", "scheduled"]:
                    self.unresolved_events.add(ev.event_id)
                continue
                
            if effective_date >= start_date:
                base_amount = self.converter.convert(ev.amount, ev.currency, effective_date)
                net_amount = -base_amount if ev.direction == "debit" else base_amount
                
                forecast.append({
                    "event_id": ev.event_id,
                    "date": effective_date,
                    "amount": net_amount,
                    "category": ev.category,
                    "description": ev.description,
                    "flexibility": ev.flexibility,
                    "minimum_allowed_amount": ev.minimum_allowed_amount,
                    "currency": ev.currency,
                    "is_explicit": True
                })
                
                if key not in latest_explicit or effective_date > latest_explicit[key]:
                    latest_explicit[key] = effective_date
                    
        recurring = self._infer_recurrence()
        for key, rec in recurring.items():
            user_id, category, description, direction, currency = key
            
            # If the group has unresolved amounts, we cannot safely project
            # (Unresolved amounts were added to unresolved_events during the loop above)
            
            anchor_date = rec["latest_date"]
            if key in latest_explicit and latest_explicit[key] > anchor_date:
                anchor_date = latest_explicit[key]
                
            current_proj_date = anchor_date + rec["interval"]
            synthetic_idx = 1
            while current_proj_date <= end_date:
                if current_proj_date >= start_date:
                    base_amount = self.converter.convert(rec["projected_amount"], currency, current_proj_date)
                    net_amount = -base_amount if direction == "debit" else base_amount
                    
                    forecast.append({
                        "event_id": f"synthetic_{category}_{synthetic_idx}",
                        "date": current_proj_date,
                        "amount": net_amount,
                        "category": category,
                        "description": description,
                        "flexibility": rec["flexibility"],
                        "minimum_allowed_amount": rec["minimum_allowed_amount"],
                        "currency": currency,
                        "is_explicit": False
                    })
                current_proj_date += rec["interval"]
                synthetic_idx += 1
                
        forecast.sort(key=lambda x: x["date"])
        return forecast
