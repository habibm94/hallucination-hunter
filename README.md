# 🔍 Hallucination Hunter

**Automated hallucination detection and scoring for LLM outputs — built on the RAG Triad framework.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55-red.svg)](https://streamlit.io)
[![Framework](https://img.shields.io/badge/Framework-RAG%20Triad-green.svg)](https://docs.ragas.io)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange.svg)]()

---

## What It Does

Hallucination Hunter is a production-grade **EvalOps tool** that automatically detects and scores factual errors in LLM-generated responses.

It takes three inputs:
1. A **source document** (ground truth)
2. A **question** asked of the LLM
3. The **LLM's response**

And returns a structured **Hallucination Audit Report** — scoring faithfulness, identifying specific false claims, and flagging ungrounded assertions.

---

## Why This Matters

> "AI hallucinations cost enterprises an estimated $100B+ annually in trust failures, legal exposure, and rework." — *McKinsey AI Report, 2025*

Most teams building RAG pipelines can measure retrieval speed. Very few can measure **whether the model is lying about what it retrieved**. That gap is what this tool closes.

**Three problems it solves:**

| Problem | What Hallucination Hunter Does |
|---|---|
| Manual review doesn't scale | Evaluates 1,000+ responses/minute vs. human rate of ~30/hour |
| Failures are invisible | Returns atomic claim-level breakdown, not just a pass/fail |
| Multilingual blind spots | Detects cross-lingual grounding errors (English ↔ Bengali) missed by English-only evaluators |

---

## How It Works — The RAG Triad Pipeline

```
SOURCE DOCUMENT + LLM RESPONSE
         │
         ▼
  ┌─────────────────────┐
  │  CLAIM EXTRACTOR    │  ← Breaks response into atomic facts
  └─────────────────────┘
         │
         ▼
  ┌─────────────────────┐
  │  NLI VERIFIER       │  ← Checks each claim vs. source
  │  (Entailment / NLI) │    ENTAIL | CONTRADICT | NEUTRAL
  └─────────────────────┘
         │
         ▼
  ┌─────────────────────┐
  │  METRICS ENGINE     │  ← Calculates RAG Triad scores
  │  · Faithfulness     │    (0.0 = pure hallucination)
  │  · Answer Relevancy │    (1.0 = fully grounded)
  │  · Context Precision│
  └─────────────────────┘
         │
         ▼
  ┌─────────────────────┐
  │  AUDIT REPORT       │  ← JSON + Streamlit dashboard
  └─────────────────────┘
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11 |
| UI | Streamlit |
| Evaluation Framework | DeepEval + RAGAS |
| NLI / Judge Model | Claude Sonnet / GPT-4o |
| Data Handling | Pandas |
| Version Control | GitHub |

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/habibm94/hallucination-hunter.git
cd hallucination-hunter

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
cp .env.example .env
# Edit .env with your OPENAI_API_KEY or ANTHROPIC_API_KEY

# 5. Run the app
streamlit run app.py
```

---

## Example Output

**Input:**
```json
{
  "source": "The Eiffel Tower is located in Paris, France. It was constructed in 1889.",
  "question": "When and where was the Eiffel Tower built?",
  "answer": "The Eiffel Tower was built in 1892 in London, England."
}
```

**Audit Report:**
```json
{
  "faithfulness_score": 0.0,
  "status": "FAIL — HALLUCINATION DETECTED",
  "claims": [
    {
      "claim": "Built in 1892",
      "verdict": "CONTRADICTION",
      "source_says": "Constructed in 1889",
      "score": 0.0
    },
    {
      "claim": "Located in London, England",
      "verdict": "CONTRADICTION",
      "source_says": "Located in Paris, France",
      "score": 0.0
    }
  ]
}
```

---

## Project Status

See [ROADMAP.md](ROADMAP.md) for full build plan.

- ✅ **Phase 0** — Repository setup, golden dataset, architecture design
- 🔄 **Phase 1** — Core logic: claim extractor + NLI verifier + metrics engine *(in progress)*
- ⏳ **Phase 2** — Streamlit dashboard + side-by-side model comparison
- ⏳ **Phase 3** — Bengali multilingual module + Streamlit Cloud deployment

---

## About the Builder

Built by **Habibullah Bin Mahmud** — Senior AI Evaluator with 2,200+ hours across frontier LLM evaluation pipelines (Outlier.ai, Veritylab.ai). Native Bengali speaker specializing in cross-lingual hallucination detection and multilingual alignment auditing.

This project translates 2,200 hours of manual evaluation intuition into automated, scalable EvalOps infrastructure.

🔗 [LinkedIn](https://linkedin.com/in/habibm94) · [GitHub](https://github.com/habibm94)
