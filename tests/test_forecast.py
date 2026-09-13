import unittest
from datetime import date, timedelta
from code.models import FinancialProfile, FinancialEvent, ExchangeRate
from code.currency import CurrencyConverter
from code.financial_state import FinancialState
from code.forecast import Forecaster
from code.llm_extractor import ExtractedFact

class TestForecastEngine(unittest.TestCase):
    def setUp(self):
        self.profile = FinancialProfile(
            user_id="user_test",
            home_currency="USD",
            current_available_balance=1000.0,
            minimum_balance_to_keep=200.0,
            financial_priorities="",
            expense_categories_to_protect="",
            expense_categories_user_is_willing_to_reduce="dining",
            expense_categories_user_is_willing_to_stop="entertainment",
            payment_methods_user_will_consider="full_payment",
            max_installment_months=""
        )
        self.rates = [ExchangeRate(from_currency="EUR", to_currency="USD", rate_date=date(2024, 1, 10), rate=1.1)]
        self.converter = CurrencyConverter(self.rates, "USD")
        self.base_events = []
        self.req_date = date(2024, 1, 1)

    def _get_forecaster(self, events):
        state = FinancialState(self.profile, events, self.converter)
        return Forecaster(state, self.req_date)

    def test_1_affordable_today(self):
        f = self._get_forecaster([])
        self.assertEqual(f.calculate_amount_safe_to_pay(500), 500)
        self.assertTrue(f.check_safety(500)[0])

    def test_2_affordable_later_and_13_earliest_date(self):
        # Balance 1000, min 200. Req = 1500. Not affordable today.
        # Income on day 10 of 1000.
        ev = FinancialEvent("e1", "user_test", "income", "salary", "salary", "credit", 1000.0, "USD", 
                            date(2024, 1, 11), date(2024, 1, 11), "scheduled", "", "fixed", None)
        f = self._get_forecaster([ev])
        
        self.assertEqual(f.calculate_amount_safe_to_pay(1500), 800) # (1000-200) today
        self.assertEqual(f.calculate_earliest_full_payment(1500), "2024-01-11")

    def test_3_minimum_balance_constraint(self):
        f = self._get_forecaster([])
        self.assertEqual(f.calculate_amount_safe_to_pay(900), 800)
        self.assertFalse(f.check_safety(801)[0])

    def test_4_5_recurring_income_expense(self):
        # 3 past rents of 100 on 1st of month. Next should be 2024-01-01, 2024-02-01, 2024-03-01
        events = []
        for i, m in enumerate([10, 11, 12]):
            events.append(FinancialEvent(f"r{i}", "user_test", "expense", "rent", "rent", "debit", 100.0, "USD", 
                            date(2023, m, 1), date(2023, m, 1), "settled", "", "fixed", None))
        f = self._get_forecaster(events)
        
        # 3 future rents in 90 days. Total expense = 300.
        # Headroom drops by 100 each time. Min headroom is on day 90: 1000 - 300 - 200 = 500.
        self.assertEqual(f.calculate_amount_safe_to_pay(1000), 500)

    def test_6_confirmed_future_payment(self):
        ev = FinancialEvent("e1", "user_test", "expense", "tax", "tax", "debit", 300.0, "USD", 
                            date(2024, 1, 15), date(2024, 1, 15), "scheduled", "", "fixed", None)
        f = self._get_forecaster([ev])
        self.assertEqual(f.calculate_amount_safe_to_pay(1000), 500)

    def test_7_pending_credit_ignored(self):
        ev = FinancialEvent("e1", "user_test", "income", "refund", "refund", "credit", 500.0, "USD", 
                            date(2024, 1, 5), date(2024, 1, 5), "pending", "", "fixed", None)
        f = self._get_forecaster([ev])
        self.assertEqual(f.calculate_amount_safe_to_pay(1000), 800) # credit ignored

    def test_8_9_10_failed_cancelled_duplicate_ignored(self):
        events = [
            FinancialEvent("e1", "user_test", "expense", "fee", "fee", "debit", 100.0, "USD", date(2024, 1, 5), date(2024, 1, 5), "failed", "", "fixed", None),
            FinancialEvent("e2", "user_test", "expense", "fee", "fee", "debit", 100.0, "USD", date(2024, 1, 5), date(2024, 1, 5), "cancelled", "", "fixed", None),
            FinancialEvent("e3", "user_test", "expense", "fee", "fee", "debit", 100.0, "USD", date(2024, 1, 5), date(2024, 1, 5), "duplicate", "", "fixed", None)
        ]
        f = self._get_forecaster(events)
        self.assertEqual(f.calculate_amount_safe_to_pay(1000), 800)

    def test_11_missing_event_amount_handling(self):
        ev = FinancialEvent("e1", "user_test", "expense", "bill", "bill", "debit", None, "USD", 
                            date(2024, 1, 15), date(2024, 1, 15), "scheduled", "", "fixed", None)
        
        # Without fact, it's unresolved
        f = self._get_forecaster([ev])
        self.assertEqual(f.calculate_amount_safe_to_pay(1000), 0.0)
        self.assertEqual(f.calculate_earliest_full_payment(1000), "")
        
        # With fact
        state = FinancialState(self.profile, [ev], self.converter)
        state.apply_facts([ExtractedFact("update_amount", "e1", None, 300.0, None, "high", True)])
        f2 = Forecaster(state, self.req_date)
        self.assertEqual(f2.calculate_amount_safe_to_pay(1000), 500.0)

    def test_12_currency_conversion(self):
        ev = FinancialEvent("e1", "user_test", "expense", "trip", "trip", "debit", 100.0, "EUR", 
                            date(2024, 1, 10), date(2024, 1, 10), "scheduled", "", "fixed", None)
        f = self._get_forecaster([ev])
        self.assertEqual(f.calculate_amount_safe_to_pay(1000), 800 - 110) # 690

    def test_14_flexible_expense_reduction(self):
        ev = FinancialEvent("e1", "user_test", "expense", "eat", "dining", "debit", 300.0, "USD", 
                            date(2024, 1, 5), date(2024, 1, 5), "scheduled", "", "reducible", 100.0)
        f = self._get_forecaster([ev])
        
        # Without reduction, max safe is 500.
        self.assertEqual(f.calculate_amount_safe_to_pay(1000), 500)
        
        # With reduction to 100
        safe, min_head = f.check_safety(700, {"e1": 100.0}) # 700 + 100 = 800 -> hits exactly min balance
        self.assertTrue(safe)
        
    def test_15_flexible_expense_stopping(self):
        ev = FinancialEvent("e1", "user_test", "expense", "fun", "entertainment", "debit", 300.0, "USD", 
                            date(2024, 1, 5), date(2024, 1, 5), "scheduled", "", "stoppable", None)
        f = self._get_forecaster([ev])
        
        # Without stop, max safe is 500
        self.assertEqual(f.calculate_amount_safe_to_pay(1000), 500)
        
        # With stop
        safe, min_head = f.check_safety(800, {"e1": 0})
        self.assertTrue(safe)

    def test_16_forecast_horizon_boundary(self):
        # Day 91 expense should NOT be included
        ev = FinancialEvent("e1", "user_test", "expense", "far", "far", "debit", 800.0, "USD", 
                            self.req_date + timedelta(days=91), self.req_date + timedelta(days=91), "scheduled", "", "fixed", None)
        f = self._get_forecaster([ev])
        # Safe amount is 800 because the 800 expense is OUTSIDE the 90 day horizon (day 91)
        self.assertEqual(f.calculate_amount_safe_to_pay(1000), 800)

if __name__ == '__main__':
    unittest.main()
