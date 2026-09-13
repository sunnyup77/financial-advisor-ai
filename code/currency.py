from typing import List
from datetime import date
from code.models import ExchangeRate

class CurrencyConverter:
    def __init__(self, rates: List[ExchangeRate], home_currency: str):
        self.rates = rates
        self.home_currency = home_currency

    def convert(self, amount: float, from_currency: str, rate_date: date) -> float:
        if from_currency == self.home_currency:
            return amount
            
        applicable = [r for r in self.rates if r.from_currency == from_currency and r.to_currency == self.home_currency]
        if not applicable:
            raise ValueError(f"No exchange rate found for {from_currency} to {self.home_currency}")
            
        for r in applicable:
            if r.rate_date == rate_date:
                return amount * r.rate
                
        preceding = [r for r in applicable if r.rate_date < rate_date]
        if preceding:
            best = max(preceding, key=lambda r: r.rate_date)
            return amount * best.rate
            
        best = min(applicable, key=lambda r: r.rate_date)
        return amount * best.rate
