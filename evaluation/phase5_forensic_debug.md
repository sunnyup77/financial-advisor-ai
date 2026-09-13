# Phase 5 Forensic Debugging Report

## 1. Overview of 20-Sample Validation Mismatches

The 20-sample validation resulted in 0% exact match accuracy. By isolating the pipeline and manually tracing the deterministic logic using cached evidence, we have confirmed that the extraction layer (Gemini) is functioning correctly when it doesn't time out. The divergence is strictly caused by logic gaps in the deterministic Python code (Phases 3 and 4). 

### First Divergent Stages

| request_id | first_divergent_stage | expected | actual | likely_cause | file | function |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `request_04` | 90-day forecasting | `8,401,800` | `11,640,196.69` | Phase 3 recurring detection missed some past events (e.g., detecting <3 occurrences or strict interval matching), leading to an overestimated safe amount. | `code/recurring_detection.py` | `detect_recurring_events` |
| `request_04` | Candidate filtering | `wait` method | `full_payment` with changes | Phase 4 engine filters the `wait` strategy based on the profile's `allowed_methods`. However, `wait` is a temporal fallback for `full_payment`, not a merchant payment method, and should always be considered if full payment is desired but currently unaffordable. | `code/decision_engine.py` | `generate_base_candidates` |
| `request_12` | Candidate ranking | Option 33 (3 pmts) | Option 34 (1 pmt) | Phase 4 engine selected a 1-payment "installment" plan because it had a lower total cost. The ground truth likely rejects 1-payment installments if `full_payment` is forbidden by the user, or the ground truth forecast deemed it unsafe. | `code/decision_engine.py` | `rank_candidates` |
| `request_07` | Evidence extraction | N/A | HTTP 503 | Live Gemini call failed due to high demand. | `code/gemini_provider.py` | `generate_json` |
| `request_13` | Evidence extraction | N/A | Timeout | Live Gemini call timed out. | `code/gemini_provider.py` | `generate_json` |
| `request_14` | Evidence extraction | N/A | Timeout | Live Gemini call timed out. | `code/gemini_provider.py` | `generate_json` |

## 2. Top 3 Actual Bugs

### Bug 1: "Wait" Strategy Filtering (Phase 4)
- **Samples Affected:** Affects multiple samples (e.g., `request_04`, `request_01`, `request_03`, `request_08`, `request_18`).
- **Description:** The `DecisionEngine.generate_base_candidates()` method explicitly checks if `"wait" in allowed_methods` (which draws from the user's profile). However, "wait" is not a merchant payment method—it is a temporal strategy. If a user only allows `full_payment`, and they cannot afford it today but can afford it before the deadline, "wait" must be generated.
- **Evidence:** For `request_04`, the allowed methods were strictly `['full_payment']`. The engine ignored the `wait` plan completely and instead forced a `full_payment` today by applying spending changes, which violated the "no spending changes" ranking preference.
- **Files to Modify:** `code/decision_engine.py`

### Bug 2: Recurring Event Detection Under-sensitivity (Phase 3)
- **Samples Affected:** Affects almost all mismatched `amount_safe_to_pay` samples (e.g., `request_04`, `request_02`, `request_10`).
- **Description:** The Phase 3 `recurring_detection.py` logic is missing several recurring expenses that the ground truth successfully projects. For `request_04`, our engine calculated a headroom of `11,640,196.69` on the request date, while the ground truth expected `8,401,800`. This ~3.2M IDR discrepancy corresponds to perfectly valid past events (e.g., "Fresh food shop" and "Bakery and snacks") that our algorithm failed to classify as recurring, likely because they didn't meet strict interval variance checks or occurrence thresholds.
- **Evidence:** Summing the generated synthetic events in the trace for `request_04` yields ~9.8M IDR in expenses prior to the next payday, but the baseline minimum headroom should drop by ~13.1M IDR. 
- **Files to Modify:** `code/recurring_detection.py`

### Bug 3: 1-Payment Installment Plans (Phase 4)
- **Samples Affected:** Evaluated heavily on `request_12` and potentially others.
- **Description:** The dataset contains `installments` options in `payment_options.csv` that only require 1 payment (effectively a full payment). If a user strictly forbids `full_payment` but allows `installments`, selecting a 1-payment installment plan exploits a loophole. The ground truth seems to enforce that `installments` must be > 1 payment.
- **Evidence:** In `request_12`, Option 34 (1 payment of 65k) was chosen over Option 33 (3 payments totaling 67k) strictly because the total amount paid was lower. The expected output was Option 33.
- **Files to Modify:** `code/decision_engine.py`

## 3. Would switching the Gemini model help?
**No, not for the calculation errors.** The vast majority of the discrepancies are mathematically rooted in the Python deterministic logic. 
Switching the model (e.g., to `gemini-1.5-pro` or standard `gemini-1.5-flash`) might resolve the 503 and Timeout errors seen in requests 7, 13, and 14 by providing a more stable API endpoint, but it will **not** fix the 0% accuracy on the core financial calculations which are performed entirely by Python.

## 4. Existing Test-Suite Result
All 41 existing offline tests are passing because the test suite validates that the Phase 3/4 code behaves as it was *written*, not necessarily matching the edge cases in the hidden ground truth rules. The tests for recurring detection, for instance, mock perfectly spaced events, masking the interval variance bug that appears in real data.
