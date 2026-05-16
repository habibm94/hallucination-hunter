# Hallucination Hunter

Automated faithfulness evaluation for LLM outputs, built on the RAG Triad.
source document + LLM answer  →  claim extraction  →  NLI verification  →  Faithfulness Score

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![License MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)

---

## What it does

Hallucination Hunter detects when an LLM response contradicts, fabricates, or drifts from its source document. It breaks the answer into atomic claims, verifies each against the source via NLI, and returns a per-claim verdict with an aggregate Faithfulness Score.

### Faithfulness thresholds

| Score | Status | Meaning |
|-------|--------|---------|
| >= 0.85 | PASS | All or nearly all claims are grounded |
| 0.50 - 0.84 | WARNING | Some claims are ungrounded or contradicted |
| < 0.50 | FAIL | Majority of claims are hallucinated |

---

## Supported providers

| Provider | Models |
|----------|--------|
| Google Gemini | gemini-2.5-flash-lite, gemini-2.5-flash, gemini-2.5-pro |
| OpenAI | gpt-4o-mini, gpt-4o |
| Anthropic | claude-haiku-4-5, claude-sonnet-4-6 |
| Groq | llama-3.3-70b, llama-3.1-8b |

All providers are bring-your-own-key. Keys are stored in session memory only — never written to disk.

---

## Project structure
hallucination-hunter/
├── src/hallucination_hunter/
│   ├── pipeline.py          Orchestrator — wires extraction, verification, taxonomy, metrics
│   ├── extraction.py        Claim extraction via LLM
│   ├── verification.py      NLI verification — ENTAIL / CONTRADICT / NEUTRAL
│   ├── taxonomy.py          Hallucination type classifier (INTRINSIC, TEMPORAL, NUMERIC, ...)
│   ├── metrics.py           RAG Triad scoring and report assembly
│   ├── models.py            Domain types (Pydantic v2, no I/O)
│   ├── errors.py            Typed error system with stable codes
│   ├── cli.py               Command-line interface
│   └── providers/           LLM adapter layer (Gemini, OpenAI, Anthropic, Groq)
├── ui/
│   ├── audit.py             Streamlit audit page
│   └── styles.py            CSS design system
├── tests/                   Pytest suite — all tests run offline via mock provider
├── docs/
│   ├── ARCHITECTURE.md      System design and module map
│   └── ROADMAP.md           Shipped features and planned work
├── examples/
│   └── golden_dataset.json  10 labelled validation cases
├── app.py                   Streamlit entry point
├── .env.example             Environment variable template
├── pyproject.toml           Project metadata and tool config
└── requirements.txt         Runtime dependencies

---

## Quickstart

### Prerequisites

- Python 3.11+
- An API key from any supported provider. Gemini has a free tier — get one at [aistudio.google.com](https://aistudio.google.com/app/apikey).

### Install

```bash
git clone https://github.com/habibm94/hallucination-hunter.git
cd hallucination-hunter
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### Configure

```bash
cp .env.example .env
# Add your API key to .env
```

### Run tests

```bash
pip install -r requirements-dev.txt
pytest
```

All tests use a mock provider and pass fully offline.

---

## CLI usage

```bash
# Single audit
hallucination-hunter \
  --source "The Eiffel Tower is in Paris. It was built in 1889." \
  --question "Where and when was the Eiffel Tower built?" \
  --answer "The Eiffel Tower was built in 1892 in London."

# Batch audit from file
hallucination-hunter --input examples/golden_dataset.json --output report.json
```

---

## Dashboard

```bash
streamlit run app.py
```

Paste your API key in the UI, choose a provider and model, and run audits interactively. Supports single-answer and A/B comparison modes.

---

## Python API

```python
from hallucination_hunter import HallucinationHunter

hunter = HallucinationHunter()  # reads GEMINI_API_KEY from .env

report = hunter.audit(
    source="The Eiffel Tower is in Paris. It was built in 1889.",
    question="Where is the Eiffel Tower?",
    answer="The Eiffel Tower is in Berlin.",
)

print(report.status.value)          # FAIL
print(report.faithfulness_score)    # 0.0
print(report.to_dict())             # full JSON-serialisable report
```

---

## Development

```bash
pytest --cov=src/hallucination_hunter   # tests with coverage
ruff check src/ tests/                  # lint
```

---

## License

MIT — see [LICENSE](LICENSE).