"""Command-line interface for Hallucination Hunter.

Supports two audit modes:
    Single  — pass --source, --question, --answer inline.
    Batch   — pass --input pointing to a JSON array file.

Output is printed to stdout. Use --output to save a JSON report.

Usage::

    hallucination-hunter --input examples/golden_dataset.json
    hallucination-hunter --source "Paris is in France." \\
                         --question "Where is Paris?" \\
                         --answer "Paris is in Germany."
    hallucination-hunter --input data.json --output report.json
"""

from __future__ import annotations

import argparse
import json
import sys

from hallucination_hunter.models import AuditReport, Verdict
from hallucination_hunter.pipeline import HallucinationHunter
from hallucination_hunter.providers.gemini import DEFAULT_GEMINI_MODEL

_SYMBOLS: dict[str, str] = {
    Verdict.ENTAIL.value: "✓",
    Verdict.CONTRADICT.value: "✗",
    Verdict.NEUTRAL.value: "~",
}


def _print_report(report: AuditReport) -> None:
    """Render a single audit report to stdout."""
    bar = "─" * 60
    print(f"\n{bar}")
    print(f"  Status        {report.status.value}")
    print(f"  Faithfulness  {report.faithfulness_score:.3f}")
    print(
        f"  Claims        "
        f"{report.supported_claims} supported  "
        f"{report.contradicted_claims} contradicted  "
        f"{report.ungrounded_claims} ungrounded"
    )
    print(bar)
    for claim in report.claims:
        sym = _SYMBOLS.get(claim.verdict.value, "?")
        print(f"  [{sym}] {claim.verdict.value:<12} {claim.claim}")
        if claim.source_evidence:
            ev = claim.source_evidence
            if len(ev) > 80:
                ev = ev[:77] + "…"
            print(f"       Evidence: {ev!r}")
    print(f"{bar}\n")


def main() -> None:
    """Entry point registered as the ``hallucination-hunter`` script."""
    parser = argparse.ArgumentParser(
        prog="hallucination-hunter",
        description="Automated hallucination detection for LLM outputs.",
    )
    parser.add_argument("--input", metavar="FILE", help="JSON batch file to audit.")
    parser.add_argument("--source", metavar="TEXT", help="Source document (single mode).")
    parser.add_argument("--question", metavar="TEXT", help="Question asked of the LLM.")
    parser.add_argument("--answer", metavar="TEXT", help="LLM answer to audit.")
    parser.add_argument("--provider", default="gemini", metavar="NAME")
    parser.add_argument("--model", default=DEFAULT_GEMINI_MODEL, metavar="ID")
    parser.add_argument("--output", metavar="FILE", help="Save JSON report to file.")
    parser.add_argument("--api-key", default=None, metavar="KEY")
    args = parser.parse_args()

    print(f"\nHallucination Hunter  v0.1.0")
    print(f"Provider: {args.provider}  Model: {args.model}\n")

    try:
        hunter = HallucinationHunter(
            api_key=args.api_key,
            provider=args.provider,
            model=args.model,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.input:
        try:
            reports = hunter.audit_from_file(args.input)
        except FileNotFoundError:
            print(f"File not found: {args.input}", file=sys.stderr)
            sys.exit(1)

        pass_c = sum(1 for r in reports if r.status.value == "PASS")
        warn_c = sum(1 for r in reports if r.status.value == "WARNING")
        fail_c = sum(1 for r in reports if r.status.value == "FAIL")
        print(f"Batch complete: {len(reports)} audits — PASS {pass_c}  WARNING {warn_c}  FAIL {fail_c}\n")

        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                json.dump([r.to_dict() for r in reports], fh, indent=2)
            print(f"Saved to {args.output}")

    elif args.source and args.question and args.answer:
        report = hunter.audit(
            source=args.source,
            question=args.question,
            answer=args.answer,
            progress_callback=lambda msg: print(f"  → {msg}", flush=True),
        )
        _print_report(report)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                json.dump(report.to_dict(), fh, indent=2)
            print(f"Saved to {args.output}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
