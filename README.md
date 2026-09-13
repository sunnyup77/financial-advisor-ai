# HackerRank Orchestrate: Buy or Wait? 🤖💰

An autonomous, AI-powered financial decision agent built for the **HackerRank Orchestrate (September 2026)** Hackathon. This agent reconstructs a user's exact financial position from structured profiles, historical events, and unstructured multimodal evidence (messages and images) to mathematically determine whether a purchase should be paid in full, scheduled via installments, deferred, or rejected.

## 🌟 Key Features & Architecture

This solution employs a **hybrid neuro-symbolic architecture**, separating deterministic financial logic from non-deterministic LLM extraction.

1. **Deterministic Orchestration (`code/decision_engine.py`)**: A strict, mathematically sound rules engine that calculates exact safe balances over a 90-day forecast. It rigorously adheres to minimum balance constraints, recurring commitments, pending transactions, and settlement dates without hallucination.
2. **LLM Evidence Extractor (`code/llm_extractor.py`)**: Uses **Gemini 3.5 Flash-Lite** via standard REST to analyze untrusted messages and images (receipts/invoices). It extracts specific financial state changes (`update_amount`, `update_date`, `cancel_event`) using strict JSON schema adherence.
3. **Optimized Evidence Selector (`code/llm_extractor.py`)**: Implements highly efficient evidence pruning. It routes only relevant, unresolved evidence to Gemini, dramatically reducing token usage, latency, and API costs.
4. **Zero Dependencies**: The entire project is built using Python's standard library (e.g., `urllib.request`, `csv`, `json`). **No `pip install` required!**

## 📂 Repository Structure

```text
financial-advisor-ai/
├── code/
│   ├── generate_output.py      # Production runner to process 250 requests
│   ├── evaluate_samples.py     # Evaluator for public 25-sample validation
│   ├── decision_engine.py      # Core financial orchestration logic
│   ├── forecast.py             # 90-day cash flow projection engine
│   ├── pipeline.py             # End-to-end processing pipeline
│   ├── gemini_provider.py      # Lightweight REST provider for Gemini 3.5 Flash-Lite
│   └── llm_extractor.py        # Multimodal evidence extraction & caching
├── evaluation/                 # Contains usage_report.md and analysis
├── tests/                      # Comprehensive unit and regression test suite
├── .env                        # (Not included in submission) Contains GEMINI_API_KEY
├── README.md                   # This file
└── output.csv                  # The final generated predictions
```

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.9+**
- No external pip dependencies are required.

### 2. Configuration
Create a `.env` file in the repository root and add your Gemini API key:
```env
GEMINI_API_KEY="your_api_key_here"
```

### 3. Running the Production Pipeline
To process the full dataset (`dataset/requests.csv`) and generate the final `output.csv`, run:
```bash
python -m code.generate_output
```
This script will:
- Process all 250 requests strictly in order.
- Generate `output.csv` containing the final `amount_safe_to_pay`, `payment_plan`, etc.
- Generate `evaluation/usage_report.md` tracking exact API calls, cache hits, and token usage.

### 4. Running the Test Suite
The project includes a robust suite of 47 regression and unit tests to validate the engine's deterministic math, recurrence logic, and formatting compliance. Run it with:
```bash
python -m unittest discover tests
```

### 5. Running the Public Sample Evaluator
To validate the system against the 25 provided sample requests, run:
```bash
python -m code.evaluate_samples
```

## 🧠 Decision Engine Logic Highlights
- **Wait Strategy**: Successfully determines when a user cannot afford a purchase today but can safely pay in full at a future date without breaching minimum balances.
- **Installment Validation**: Rejects disallowed single-payment installments and strictly enforces the user's `max_installment_months`.
- **Spending Adjustments**: Intelligently identifies flexible, non-protected events to `reduce_to` or `stop` in order to safely unlock funds for a purchase.
- **Fail-Fast Mechanics**: Includes resilient retry mechanisms for `HTTP 429` Rate Limits, and gracefully rejects un-extractable evidence to preserve system stability.

## 📝 Usage Report
The final submission metrics (token usage, cache hits, runtime) are located in `evaluation/usage_report.md`.
