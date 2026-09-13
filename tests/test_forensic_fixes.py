import unittest
from datetime import date
from code.models import RequestData, FinancialProfile, PaymentOption, FinancialEvent
from code.financial_state import FinancialState
from code.currency import CurrencyConverter
from code.forecast import Forecaster
from code.decision_engine import DecisionEngine, CandidatePlan

class TestForensicFixes(unittest.TestCase):
    def setUp(self):
        self.profile = FinancialProfile(
            user_id="u1",
            home_currency="USD",
            current_available_balance=1000.0,
            minimum_balance_to_keep=200.0,
            financial_priorities="",
            expense_categories_to_protect="",
            expense_categories_user_is_willing_to_reduce="",
            expense_categories_user_is_willing_to_stop="",
            payment_methods_user_will_consider=["full_payment"],
            max_installment_months=""
        )
        self.converter = CurrencyConverter([], "USD")

    def test_fix1_wait_is_not_a_payment_method(self):
        # Even if "wait" is not in allowed methods, if "full_payment" is allowed,
        # wait candidate should be generated if full payment can be made later.
        
        req = RequestData(
            request_id="req_1",
            user_id="u1",
            request_date=date(2024, 1, 1),
            request_type="purchase",
            requested_amount=1500.0,
            desired_completion_date=date(2024, 1, 31),
            allows_partial_payment=False,
            request_text=""
        )
        
        # Add income on Jan 15 to make it affordable later
        events = [
            FinancialEvent("e1", "u1", "income", "Salary", "salary", "credit", 2000.0, "USD", date(2024, 1, 15), date(2024, 1, 15), "settled", "", "fixed", None)
        ]
        
        state = FinancialState(self.profile, events, self.converter)
        forecaster = Forecaster(state, req.request_date)
        engine = DecisionEngine(req, state, forecaster, [])
        
        candidates = engine.generate_base_candidates()
        
        methods = [c.method for c in candidates]
        self.assertIn("wait", methods)
        self.assertIn("full_payment", methods)

    def test_fix2_reject_1_payment_installments_if_full_not_allowed(self):
        self.profile.payment_methods_user_will_consider = ["installments"]
        
        req = RequestData(
            request_id="req_2",
            user_id="u1",
            request_date=date(2024, 1, 1),
            request_type="purchase",
            requested_amount=500.0,
            desired_completion_date=date(2024, 1, 31),
            allows_partial_payment=False,
            request_text=""
        )
        
        options = [
            PaymentOption("opt1", "req_2", "installments", 500.0, 1, date(2024, 1, 1), 0, 0, 500.0),
            PaymentOption("opt2", "req_2", "installments", 250.0, 2, date(2024, 1, 1), 14, 0, 500.0)
        ]
        
        state = FinancialState(self.profile, [], self.converter)
        forecaster = Forecaster(state, req.request_date)
        engine = DecisionEngine(req, state, forecaster, options)
        
        candidates = engine.generate_base_candidates()
        
        installment_cands = [c for c in candidates if c.method == "installments"]
        self.assertEqual(len(installment_cands), 1)
        self.assertEqual(installment_cands[0].payment_option_id, "opt2")

    def test_fix3_recurring_detection_with_2_occurrences(self):
        # 2 occurrences exactly 28 days apart, and globally >=3 occurrences (simulated by mocking global_counts)
        events = [
            FinancialEvent("e1", "u1", "expense", "Bakery and snacks", "dining", "debit", 100.0, "USD", date(2024, 1, 1), date(2024, 1, 1), "settled", "", "fixed", None),
            FinancialEvent("e2", "u1", "expense", "Bakery and snacks", "dining", "debit", 100.0, "USD", date(2024, 1, 29), date(2024, 1, 29), "settled", "", "fixed", None)
        ]
        
        state = FinancialState(self.profile, events, self.converter)
        # Mock the global counts to pretend it appears 3 times globally
        state._global_counts = {"Bakery and snacks": 3}
        
        # Test infer_recurrence directly
        recurring = state._infer_recurrence()
        
        key = ("u1", "dining", "Bakery and snacks", "debit", "USD")
        self.assertIn(key, recurring)
        self.assertEqual(recurring[key]["interval"].days, 28)

if __name__ == '__main__':
    unittest.main()
