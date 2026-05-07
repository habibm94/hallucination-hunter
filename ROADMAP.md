# Hallucination Hunter — Build Roadmap

**4-Week Sprint to a Production-Grade EvalOps Portfolio Project**

---

## Phase 0: Foundation ✅ COMPLETE
*Week 0 — Setup & Architecture*

- [x] Repository created and named
- [x] Project architecture designed (RAG Triad pipeline)
- [x] Tech stack selected (Python + Streamlit + DeepEval + RAGAS)
- [x] Golden dataset defined (examples/golden_dataset.json)
- [x] Requirements file populated
- [x] README written (recruiter-facing)
- [x] .gitignore configured

---

## Phase 1: Core Logic Engine 🔄 IN PROGRESS
*Week 1–2 — The Brain*

### Claim Extractor
- [ ] `extractor.py` — LLM-based atomic claim extraction
- [ ] System prompt for claim decomposition
- [ ] Output: list of atomic string claims
- [ ] Unit test: 5 cases from golden dataset

### NLI Verifier
- [ ] `verifier.py` — cross-encoder or LLM-as-Judge entailment
- [ ] Three-label logic: ENTAIL / CONTRADICT / NEUTRAL
- [ ] Score mapping: 1.0 / 0.0 / 0.5
- [ ] Unit test: verify all claims from golden dataset

### Metrics Engine
- [ ] `scorer.py` — RAG Triad metric calculation
- [ ] Faithfulness Score = supported_claims / total_claims
- [ ] Answer Relevancy Score (LLM judge)
- [ ] Context Precision Score (retriever quality)
- [ ] Output: structured JSON audit report

### Integration
- [ ] `hallucination_hunter.py` — main pipeline (extractor → verifier → scorer)
- [ ] CLI interface: `python hallucination_hunter.py --input examples/test.json`
- [ ] JSON report output

**Phase 1 Definition of Done:**
Running `python hallucination_hunter.py --input examples/golden_dataset.json`
produces a correct audit report for all 10 test cases.

---

## Phase 2: Streamlit Dashboard ⏳ PLANNED
*Week 3 — The Interface*

- [ ] `app.py` — Streamlit UI
- [ ] Input panel: paste source, question, answer
- [ ] Results panel: Faithfulness score + claim breakdown table
- [ ] Visual: color-coded claim verdicts (green/red/yellow)
- [ ] Side-by-side comparison mode (two models vs. same source)
- [ ] Export: download audit as JSON or CSV
- [ ] Batch mode: upload CSV of test cases

**Phase 2 Definition of Done:**
A non-technical person can paste an LLM response and get a hallucination
score in under 10 seconds, with no terminal interaction required.

---

## Phase 3: Bengali Module + Deployment ⏳ PLANNED
*Week 4 — The Differentiator*

### Bengali Multilingual Module
- [ ] `bengali_checker.py` — cross-lingual grounding auditor
- [ ] Detect register drift (Sadhu Bhasha vs. Cholitobhasha mixing)
- [ ] Flag code-switching failures (Bengali claim ↔ English source mismatch)
- [ ] Cross-lingual date/number hallucination detection
- [ ] Test dataset: 5 Bengali-specific cases (dates, proper nouns, numbers)

### Deployment
- [ ] Streamlit Community Cloud deployment (public URL)
- [ ] `.env.example` with API key placeholder
- [ ] Final README update with live demo link
- [ ] 2-minute demo video recorded and linked

**Phase 3 Definition of Done:**
A recruiter at Anthropic, Mercor, or Cohere can open the live URL,
paste an LLM response, and see a hallucination audit in their browser
with no setup required.

---

## Known Gaps & Future Work

| Gap | Plan |
|---|---|
| Batch processing (1000+ responses/min) | Add async processing in v2 |
| Cost optimization | Add Llama 3.1 70B via Groq as free judge alternative |
| Bengali safety audit mode | Extend Bengali module in v2 |
| CI/CD pipeline | GitHub Actions for automated testing |

---

## Architecture Diagram

```
INPUT
  │
  ├── source (str)       ← Ground truth document
  ├── question (str)     ← What was asked
  └── answer (str)       ← LLM response to audit
         │
         ▼
   extractor.py
   ClaimExtractor.extract()
         │
         ▼
   verifier.py
   NLIVerifier.verify()
         │
         ▼
   scorer.py
   MetricsEngine.score()
         │
         ▼
OUTPUT: AuditReport (JSON)
  │
  ├── faithfulness_score (float)
  ├── answer_relevancy_score (float)
  ├── context_precision_score (float)
  ├── status (PASS / FAIL / WARNING)
  └── claims[]
        ├── claim (str)
        ├── verdict (ENTAIL / CONTRADICT / NEUTRAL)
        ├── score (float)
        └── source_evidence (str)
```
