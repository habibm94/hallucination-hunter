# Architecture

## Design principles

1. **Provider-agnostic core.** No file outside `providers/` imports any
   third-party SDK. Adding a new LLM vendor is a contained change.
2. **Pure domain models.** `models.py` has no I/O and no external
   dependencies beyond Pydantic. It is fully unit-testable.
3. **Failure-safe verification.** Parse errors and unknown verdicts fall
   back to NEUTRAL rather than raising. A single bad response cannot
   crash a batch audit.
4. **Lightweight runtime.** No local model weights, no GPU dependency.
   Memory footprint is dominated by the Streamlit baseline (~150 MB).
5. **Test-first.** Every service has unit coverage. Integration tests use
   a `FakeProvider` to exercise the full pipeline without network calls.

## Module map

```
              ┌────────────────────────────────────────┐
              │              cli.py                    │
              │   argparse  +  load_dotenv  +  main    │
              └──────────────────┬─────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │       pipeline.py       │
                    │   HallucinationHunter   │
                    └────┬──────────┬─────────┘
                         │          │
        ┌────────────────┘          └─────────────────┐
        │                                              │
┌───────▼──────────┐  ┌──────────────────┐  ┌─────────▼────────┐
│  extraction.py   │  │   metrics.py     │  │ verification.py  │
│ ClaimExtractor   │  │  MetricsEngine   │  │   NLIVerifier    │
└───────┬──────────┘  └──────────────────┘  └─────────┬────────┘
        │                                              │
        └──────────────────┐         ┌────────────────┘
                           │         │
                  ┌────────▼─────────▼─────────┐
                  │       providers/           │
                  │   ┌─────────┐  ┌────────┐  │
                  │   │  base   │  │ gemini │  │
                  │   └─────────┘  └────────┘  │
                  └────────────────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  models.py   │
                       │   (no I/O)   │
                       └──────────────┘
```

## Data flow

A single audit request flows through the pipeline as follows:

1. **`pipeline.HallucinationHunter.audit()`** receives `(source, question, answer)`.
2. The pipeline calls **`ClaimExtractor.extract(answer)`**, which prompts
   the provider to decompose the answer into a list of atomic claims.
3. For each claim, **`NLIVerifier.verify(claim, source)`** prompts the
   provider for an entailment classification and parses the response into
   a `ClaimResult`.
4. **`MetricsEngine.build_report()`** computes faithfulness, derives the
   pass/warning/fail status, and assembles an `AuditReport`.
5. The CLI or UI consumes `AuditReport.to_dict()` for serialization or
   rendering.

## Adding a new provider

1. Create `src/hallucination_hunter/providers/<name>.py`.
2. Subclass `LLMProvider` and implement `name` and `call()`.
3. Register the class in `_PROVIDER_REGISTRY` inside
   `src/hallucination_hunter/providers/__init__.py`.
4. Add unit tests using the `FakeProvider` pattern from `conftest.py`.

No other module needs to change.

## Resource budget

| Resource | Budget |
|---|---|
| RAM (CLI) | < 100 MB |
| RAM (Streamlit UI, planned) | < 250 MB |
| Disk (installed) | < 100 MB |
| Network per audit | ~10 KB request, ~5 KB response per LLM call |
| LLM calls per audit | 1 (extraction) + N (verification, where N = claim count) |

## Security model

- API keys are read from environment variables or `.env` files. They are
  never persisted to disk by the application.
- The planned UI will store user-supplied keys in Streamlit's
  `session_state`, which lives only in the running process and is cleared
  when the browser tab closes.
- Audit inputs (source, question, answer) are sent to the configured
  provider for inference. Users should not paste credentials, PII, or
  sensitive data into audit fields unless their provider's data-handling
  policy is acceptable.
- The `.gitignore` excludes `.env`, `*.key`, and Streamlit secrets files
  from version control.
