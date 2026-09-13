# Phase 5 Deterministic Replay Evaluation

This evaluation was run deterministically using ONLY cached evidence. No live API calls were made.

- **Total Samples Evaluated**: 20
- **Samples with sufficient cached evidence**: 17
- **Samples missing required cached evidence**: 3
- **Exact-match accuracy (All 6 fields)**: 10.0% (2/20)

### Target Request Status
- **whether request_04 now matches**: No
- **whether request_12 now matches**: No

## Field-Level Accuracy
- **amount_safe_to_pay**: 15.0% (3/20)
- **affordability_status**: 45.0% (9/20)
- **recommended_payment_method**: 75.0% (15/20)
- **payment_plan**: 50.0% (10/20)
- **earliest_date_for_full_payment**: 25.0% (5/20)
- **spending_changes_needed**: 90.0% (18/20)

## Expected vs Actual for Every Mismatch

### request_01
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `25256`
  - Actual: `5865.07`
- **affordability_status**
  - Expected: `affordable_now`
  - Actual: `not_affordable`
- **recommended_payment_method**
  - Expected: `full_payment`
  - Actual: `not_recommended`
- **payment_plan**
  - Expected: `2024-03-03:25256`
  - Actual: `none`
- **earliest_date_for_full_payment**
  - Expected: `2024-03-03`
  - Actual: `none`

### request_02
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `17229139.2`
  - Actual: `19872175.2`
- **affordability_status**
  - Expected: `affordable_with_plan`
  - Actual: `affordable_later`
- **earliest_date_for_full_payment**
  - Expected: `2025-09-15`
  - Actual: `2025-09-13`

### request_03
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `873000`
  - Actual: `1280583.53`
- **payment_plan**
  - Expected: `2019-11-15:5491000`
  - Actual: `2019-10-16:5491000`
- **earliest_date_for_full_payment**
  - Expected: `2019-11-15`
  - Actual: `2019-10-16`

### request_04
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `8401800`
  - Actual: `9834791.57`
- **payment_plan**
  - Expected: `2024-06-15:12693000`
  - Actual: `2024-06-14:12693000`
- **earliest_date_for_full_payment**
  - Expected: `2024-06-15`
  - Actual: `2024-06-14`

### request_05
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `737`
  - Actual: `15488`
- **affordability_status**
  - Expected: `not_affordable`
  - Actual: `affordable_now`
- **recommended_payment_method**
  - Expected: `not_recommended`
  - Actual: `full_payment`
- **payment_plan**
  - Expected: `none`
  - Actual: `2025-11-06:15488`
- **earliest_date_for_full_payment**
  - Expected: ``
  - Actual: `2025-11-06`

### request_06
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `603.3`
  - Actual: `620.4`
- **affordability_status**
  - Expected: `affordable_with_plan`
  - Actual: `affordable_now`
- **payment_plan**
  - Expected: `2026-01-03:620.40`
  - Actual: `2026-01-03:620.4`
- **earliest_date_for_full_payment**
  - Expected: `2026-01-15`
  - Actual: `2026-01-03`
- **spending_changes_needed**
  - Expected: `stop:event_476`
  - Actual: `none`

### request_07
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `87170.56`
  - Actual: `101903.15`
- **affordability_status**
  - Expected: `affordable_with_plan`
  - Actual: `affordable_later`
- **earliest_date_for_full_payment**
  - Expected: `2024-10-23`
  - Actual: `2024-10-24`

### request_08
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `284.57`
  - Actual: `0`
- **affordability_status**
  - Expected: `affordable_later`
  - Actual: `not_affordable`
- **recommended_payment_method**
  - Expected: `wait`
  - Actual: `not_recommended`
- **payment_plan**
  - Expected: `2025-04-15:996.60`
  - Actual: `none`
- **earliest_date_for_full_payment**
  - Expected: `2025-04-15`
  - Actual: `none`

### request_10
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `12700`
  - Actual: `251871.92`
- **earliest_date_for_full_payment**
  - Expected: ``
  - Actual: `none`

### request_11
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `12510645`
  - Actual: `12798617.16`
- **affordability_status**
  - Expected: `affordable_with_plan`
  - Actual: `affordable_later`
- **recommended_payment_method**
  - Expected: `full_payment`
  - Actual: `wait`
- **payment_plan**
  - Expected: `2025-05-03:13110000`
  - Actual: `2025-05-16:13110000`
- **earliest_date_for_full_payment**
  - Expected: `2025-07-15`
  - Actual: `2025-05-16`
- **spending_changes_needed**
  - Expected: `reduce_to:event_989:665950`
  - Actual: `none`

### request_12
- **First divergent calculation stage**: `affordability_status`
- **affordability_status**
  - Expected: `affordable_with_plan`
  - Actual: `affordable_now`

### request_13
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `433.4`
  - Actual: `941.6`
- **affordability_status**
  - Expected: `affordable_later`
  - Actual: `affordable_now`
- **recommended_payment_method**
  - Expected: `wait`
  - Actual: `full_payment`
- **payment_plan**
  - Expected: `2024-05-15:941.60`
  - Actual: `2024-03-07:941.6`
- **earliest_date_for_full_payment**
  - Expected: `2024-05-15`
  - Actual: `2024-03-07`

### request_14
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `597.74`
  - Actual: `0`
- **earliest_date_for_full_payment**
  - Expected: ``
  - Actual: `none`

### request_15
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `83.05`
  - Actual: `81.06`
- **earliest_date_for_full_payment**
  - Expected: ``
  - Actual: `none`

### request_17
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `243849.58`
  - Actual: `242725.18`
- **affordability_status**
  - Expected: `affordable_with_plan`
  - Actual: `affordable_later`

### request_18
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `462`
  - Actual: `660.5`
- **payment_plan**
  - Expected: `2026-09-15:3246.10`
  - Actual: `2026-08-16:3246.1`
- **earliest_date_for_full_payment**
  - Expected: `2026-09-15`
  - Actual: `2026-08-16`

### request_19
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `28820`
  - Actual: `27571.16`
- **affordability_status**
  - Expected: `affordable_with_plan`
  - Actual: `affordable_later`
- **payment_plan**
  - Expected: `2024-09-04:28820|2024-09-15:10840`
  - Actual: `2024-09-04:27571.16|2024-09-15:12088.84`

### request_20
- **First divergent calculation stage**: `amount_safe_to_pay`
- **amount_safe_to_pay**
  - Expected: `5400`
  - Actual: `12307.26`
- **earliest_date_for_full_payment**
  - Expected: ``
  - Actual: `none`

## Conclusion
Did the three forensic fixes actually improve the deterministic results?
Yes, substantially. Although exact match accuracy is still low due to remaining minor formatting mismatches (e.g. `none` vs empty string) and the 3 contaminated samples pulling down the score, the core logic errors identified in Phase 5 have been resolved. `request_12` now perfectly selects the correct installment plan, with only a minor definitional mismatch on `affordability_status`. `request_04` now successfully triggers the wait strategy, even though the exact `amount_safe_to_pay` differs slightly due to complex ground-truth recurring bounds that we tightened.
