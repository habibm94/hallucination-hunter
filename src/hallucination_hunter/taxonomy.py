"""Hallucination taxonomy classifier."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from hallucination_hunter.errors import ParseError, make_error
from hallucination_hunter.models import HallucinationType, HallucinationTag

if TYPE_CHECKING:
    from hallucination_hunter.models import ClaimResult, Verdict
    from hallucination_hunter.providers.base import LLMProvider


CLASSIFIER_PROMPT_TEMPLATE = """You are an evaluation specialist classifying hallucinations in an LLM response.

Given a CLAIM extracted from an LLM answer, the SOURCE document it was supposed to be grounded in, and the VERDICT (whether the claim contradicts, is unsupported by, or is supported by the source), classify what TYPES of hallucination are present.

Use these categories. A single claim may carry MULTIPLE types.

  INTRINSIC   - The claim directly contradicts the source.
  EXTRINSIC   - The claim adds info not present in the source.
  ENTITY      - A named entity (person, place, organization) is wrong or fabricated.
  TEMPORAL    - A date, year, time, or temporal sequence is wrong.
  NUMERIC     - A number, quantity, unit, percentage, or measurement is wrong.
  CITATION    - The claim cites a source or reference that does not exist.
  LOGICAL     - The claim is internally inconsistent or violates basic logic.

If the verdict is ENTAIL (claim is supported), return an empty types list.

For ENTITY, TEMPORAL, NUMERIC, and CITATION, provide a short explanation: "<what answer said>, not <what source says>". Under 25 words.

For INTRINSIC, EXTRINSIC, and LOGICAL, no explanation needed.

OUTPUT FORMAT (strict JSON, no preamble, no markdown fences):
{{"types": [{{"type": "TEMPORAL", "explanation": "Answer said 1972, source says 1971"}}, {{"type": "INTRINSIC", "explanation": ""}}]}}

If no hallucination (verdict is ENTAIL):
{{"types": []}}

---

SOURCE:
{source}

CLAIM:
{claim}

VERDICT: {verdict}

Classify now. Return JSON only.
"""


class TaxonomyClassifier:
    """Classifies the hallucination types present in a single claim."""

    def __init__(self, llm: "LLMProvider") -> None:
        self._llm = llm

    def classify(
        self,
        claim: str,
        verdict: "Verdict",
        source: str,
    ) -> list[HallucinationTag]:
        """Return the list of hallucination types present in this claim."""
        if verdict.value == "ENTAIL":
            return []

        prompt = CLASSIFIER_PROMPT_TEMPLATE.format(
            source=source,
            claim=claim,
            verdict=verdict.value,
        )

        raw = self._llm.call(prompt)
        return self._parse_response(raw, claim=claim, verdict=verdict.value)

    def classify_all(
        self,
        claims: list["ClaimResult"],
        source: str,
    ) -> list[list[HallucinationTag]]:
        """Classify a batch of claims. Returns parallel list of tag-lists."""
        return [
            self.classify(c.claim, c.verdict, source)
            for c in claims
        ]

    @staticmethod
    def _parse_response(
        raw: str,
        *,
        claim: str,
        verdict: str,
    ) -> list[HallucinationTag]:
        """Parse the JSON response into HallucinationTag objects."""
        cleaned = TaxonomyClassifier._strip_fences(raw).strip()
        if not cleaned:
            return []

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ParseError(
                make_error(
                    "HH-PARSE-001",
                    context={
                        "stage": "taxonomy",
                        "claim": claim[:120],
                        "verdict": verdict,
                        "raw": cleaned[:200],
                        "underlying": str(e),
                    },
                    message_override=(
                        "Taxonomy classifier returned malformed JSON."
                    ),
                )
            ) from e

        types_raw = data.get("types", []) if isinstance(data, dict) else []
        if not isinstance(types_raw, list):
            return []

        tags: list[HallucinationTag] = []
        seen: set[HallucinationType] = set()
        for item in types_raw:
            if not isinstance(item, dict):
                continue
            type_str = str(item.get("type", "")).strip().upper()
            try:
                hh_type = HallucinationType(type_str)
            except ValueError:
                continue
            if hh_type in seen:
                continue
            seen.add(hh_type)
            explanation = str(item.get("explanation", "")).strip()
            if len(explanation) > 200:
                explanation = explanation[:200].rstrip() + "..."
            tags.append(HallucinationTag(type=hh_type, explanation=explanation))

        return tags

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove ```json ... ``` fences if the LLM wrapped its output."""
        m = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
        if m:
            return m.group(1)
        return text
