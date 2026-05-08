# Roadmap

This document tracks the evolution of Hallucination Hunter from its current
core to a full-featured evaluation platform.

## Shipped

- **Core pipeline.** Claim extraction, NLI verification, and RAG Triad metrics.
- **Provider abstraction.** Pluggable adapter layer with a registry-based factory.
- **Gemini adapter.** Production-ready provider with rate-limit handling and
  exponential backoff.
- **CLI.** Single-audit and batch-audit modes with text and JSON output.
- **Test suite.** Pytest coverage of models, providers, services, metrics,
  and end-to-end pipeline behaviour, using a fake provider for determinism.
- **Golden dataset.** Ten validation cases spanning grounded, contradicted,
  and ungrounded answers.

## In development

### Additional providers

- OpenAI adapter (`gpt-4o-mini`, `gpt-4o`)
- Anthropic adapter (`claude-haiku-4-5`, `claude-sonnet-4-6`)
- xAI Grok adapter (`grok-2-latest`)

Each provider implements the same `LLMProvider` protocol. No changes to
evaluation logic are required.

### Streamlit dashboard

- Interactive UI for single-audit and batch workflows
- Bring-your-own-key flow with session-scoped credential storage
- Provider and model selector on the configuration panel
- Visual results: per-claim verdict cards, score gauges, evidence highlighting
- Export: JSON and CSV download

### Bengali linguistic module

- Cross-lingual grounding checks for Bengali source / English answer pairs
  and the reverse
- Register-drift detection (Sadhu Bhasha vs. Cholitobhasha)
- Code-switching audit for "Bengali only" instruction adherence
- Native script enforcement via Unicode-range validation

## Planned

### Performance

- Async batch processing (concurrent claim verification)
- Response caching for repeated source/claim pairs
- Configurable concurrency limits per provider

### Evaluation depth

- Answer Relevancy metric (currently placeholder)
- Context Precision metric for RAG pipelines with retriever traces
- Configurable scoring rubrics for domain-specific audits

### Observability

- Structured logging to JSON
- Optional integration with LangSmith and Weights & Biases for trace export
- CI-friendly exit codes and summary reports

## Out of scope (for now)

- Local model inference. The architecture intentionally avoids loading any
  models into memory. All inference is delegated to provider APIs.
- Fine-tuning. This tool evaluates models. It does not train them.
- A public hosted demo. The tool is designed for local-first use to keep
  user credentials on their own machine.
