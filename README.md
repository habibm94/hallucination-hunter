# Hallucination Hunter

**Automated faithfulness evaluation for LLM outputs — built on the RAG Triad.**

```
source document + LLM answer  →  Faithfulness Score  →  Claim-level audit report
```

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![License MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest-brightgreen)](tests/)
[![Status](https://img.shields.io/badge/status-active%20development-orange)]()

---

## Overview

Hallucination Hunter is a local-first EvalOps tool that detects when an LLM response
contradicts, invents, or drifts away from its source document.

It implements a **three-stage judge pipeline**:

```
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│  Claim Extractor   │────▶│   NLI Verifier     │────▶│  Metrics Engine    │
│                    │     │                    │     │                    │
│  Breaks answer     │     │  Checks each claim │     │  Faithfulness      │
│  into atomic facts │     │  vs. source doc    │     │  = supported /     │
│                    │     │                    │     │    total claims     │
│  → list of claims  │     │  ENTAIL → 1.0      │     │                    │
│                    │     │  NEUTRAL → 0.5     │     │  AuditReport       │
│                    │     │  CONTRADICT → 0.0  │     │  (JSON or UI)      │
└────────────────────┘     └────────────────────┘     └────────────────────┘
```

### Faithfulness Thresholds

| Score | Status | Meaning |
|-------|--------|---------|
| ≥ 0.85 | ✅ PASS | All or nearly all claims are grounded in the source |
| 0.50 – 0.84 | ⚠️ WARNING | Some claims are ungrounded or contradicted |
| < 0.50 | ❌ FAIL | Majority of claims are hallucinated |

---

## Project Structure

```
hallucination-hunter/
├── src/hallucination_hunter/
│   ├── __init__.py              Public API
│   ├── models.py                Domain types (Pydantic v2)
│   ├── pipeline.py              Main orchestrator
│   ├── cli.py                   Command-line interface
│   ├── core/
│   │   ├── extractor.py         Claim extraction engine
│   │   ├── verifier.py          NLI verification engine
│   │   └── scorer.py            RAG Triad metrics
│   └── providers/
│       ├── base.py              Abstract provider contract
│       ├── gemini.py            Google Gemini adapter
│       └── __init__.py          Provider registry + factory
├── tests/
│   ├── conftest.py              Shared fixtures + MockProvider
│   ├── test_models.py
│   ├── test_scorer.py
│   ├── test_extractor.py
│   ├── test_verifier.py
│   └── test_providers.py
├── examples/
│   └── golden_dataset.json      10 labelled test cases
├── .env.example                 Environment template
├── pyproject.toml               Project metadata + tool config
├── requirements.txt             Pinned runtime dependencies
└── requirements-dev.txt         Dev and test dependencies
```

---

## Quickstart

### Prerequisites

- Python 3.11 or higher
- A free Gemini API key — get one at [aistudio.google.com](https://aistudio.google.com/app/apikey)
  (no credit card required · 1 000 free requests/day on `gemini-2.5-flash-lite`)

### Install

```bash
git clone https://github.com/habibm94/hallucination-hunter.git
cd hallucination-hunter

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements-dev.txt
pip install -e .
```

### Configure

```bash
cp .env.example .env
# Edit .env — set GEMINI_API_KEY=AIzaSy...
```

### Run tests (no API key needed)

```bash
pytest
```

All tests use mock providers and pass fully offline.

### Run your first audit

**Single audit:**
```bash
hallucination-hunter \
  --source "The Eiffel Tower is in Paris. It was built in 1889." \
  --question "Where and when was the Eiffel Tower built?" \
  --answer "The Eiffel Tower was built in 1892 in London."
```

**Batch audit from file:**
```bash
hallucination-hunter --input examples/golden_dataset.json --output report.json
```

**Sample output:**
```
Hallucination Hunter  v0.1.0
Provider: gemini  Model: gemini-2.5-flash-lite

  → Extracting claims …
  → Verifying 2 claim(s) …
  → Calculating metrics …

────────────────────────────────────────────────────────────
  Status        FAIL
  Faithfulness  0.000
  Claims        0 supported  2 contradicted  0 ungrounded
────────────────────────────────────────────────────────────
  [✗] CONTRADICT  The Eiffel Tower was built in 1892.
       Evidence: 'constructed in 1889'
  [✗] CONTRADICT  The Eiffel Tower is in London.
       Evidence: 'located in Paris, France'
────────────────────────────────────────────────────────────
```

---

## Python API

```python
from hallucination_hunter import HallucinationHunter

hunter = HallucinationHunter()      # reads GEMINI_API_KEY from .env

report = hunter.audit(
    source="The Eiffel Tower is in Paris. It was built in 1889.",
    question="Where is the Eiffel Tower?",
    answer="The Eiffel Tower is in Berlin.",
)

print(report.faithfulness_score)    # 0.0
print(report.status.value)          # FAIL
print(report.to_dict())             # full JSON-serialisable report
```

**Batch from file:**
```python
reports = hunter.audit_from_file("examples/golden_dataset.json")
for r in reports:
    print(r.status.value, r.faithfulness_score)
```

---

## Build Steps

| Step | Description | Status |
|------|-------------|--------|
| 1 | Project structure, models, provider abstraction | ✅ Done |
| 2 | Gemini provider adapter | ✅ Done |
| 3 | Claim extraction engine | ✅ Done |
| 4 | NLI verification engine | ✅ Done |
| 5 | Metrics engine + CLI | ✅ Done |
| 6 | Answer relevancy metric | ⏳ Next |
| 7 | Context precision metric | ⏳ Planned |
| 8 | Streamlit dashboard + BYOK UI | ⏳ Planned |
| 9 | Multi-provider support (OpenAI, Anthropic, Grok) | ⏳ Planned |
| 10 | Bengali multilingual failure mode detection | ⏳ Planned |
| 11–20 | Batch UI, export, comparison view, performance | ⏳ Planned |

---

## Supported Providers

| Provider | Development | Dashboard (Step 9) |
|----------|-------------|-------------------|
| Gemini (Google) | ✅ Default | ✅ Planned |
| OpenAI | — | ✅ Planned |
| Anthropic Claude | — | ✅ Planned |
| Grok (xAI) | — | ✅ Planned |

---

## Development

```bash
# Tests with coverage report
pytest --cov=src/hallucination_hunter

# Lint
ruff check src/ tests/

# Editable install
pip install -e .[dev]
```

---

## License

MIT — see [LICENSE](LICENSE).
