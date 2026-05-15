@'
"""Hallucination taxonomy classifier.

Given a claim, its verdict against a source, and the source itself, classify
the *type* of hallucination present. A single claim can carry multiple types
simultaneously: a claim like "the war was in 1972 by the British" against a
source saying "1971 by the Pakistani army" is Temporal AND Entity AND Intrinsic.

Seven categories (claim-level, per Ji et al. 2023 NLG hallucination survey):

  INTRINSIC   - Contradicts the source directly
  EXTRINSIC   - Adds information not present in source (unverifiable)
  ENTITY      - Wrong named entity (person, place, organization)
  TEMPORAL    - Wrong date, time, or sequence
  NUMERIC     - Wrong number, quantity, unit, or measurement
  CITATION    - Fabricated reference, source, or attribution
  LOGICAL     - Internally inconsistent reasoning

Classification is performed by an LLM (LLM-as-judge pattern). The classifier
returns a list of types per claim plus a short explanation for the specific
detail-level types (ENTITY, TEMPORAL, NUMERIC, CITATION). INTRINSIC,
EXTRINSIC, and LOGICAL are structural categories and carry no explanation.
"""

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

Use these categories. A single claim may carry MULTIPLE types — apply every type that fits.

  INTRINSIC   - The claim directly contradicts the source. Applies when verdict is CONTRADICT.
  EXTRINSIC   - The claim adds info not present in the source. Applies when verdict is NEUTRAL and the added info is concrete (not opinion).
  ENTITY      - A named entity (person, place, organization, product) is wrong or fabricated.
  TEMPORAL    - A date, year, time, or temporal sequence is wrong.
  NUMERIC     - A number, quantity, unit, percentage, or measurement is wrong.
  CITATION    - The claim cites a source, section, or reference that does not exist in the source.
  LOGICAL     - The claim is internally inconsistent or violates basic logic.

If the verdict is ENTAIL (claim is supported), return an empty types list. The claim is not hallucinated.

For ENTITY, TEMPORAL, NUMERIC, and CITATION, provide a short explanation in the form: "<what the answer said>, not <what the source says>". Keep explanations under 25 words.

For INTRINSIC, EXTRINSIC, and LOGICAL, no explanation is needed — they are structural categories.

OUTPUT FORMAT (strict JSON, no preamble, no markdown fences):
{{
  "types": [
    {{"type": "TEMPORAL", "explanation": "Answer said 1972, source says 1971"}},
    {{"type": "ENTITY", "explanation": "Answer said British army, source says Pakistani army"}},
    {{"type": "INTRINSIC", "explanation": ""}}
  ]
}}

If no hallucination types apply (verdict is ENTAIL or claim is fully supported):
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
    """Classifies the hallucination types present in a single claim.

    Uses the same LLM provider as the rest of the pipeline (LLM-as-judge).
    Stateless — one instance can classify many claims.
    """

    def __init__(self, llm: "LLMProvider") -> None:
        self._llm = llm

    def classify(
        self,
        claim: str,
        verdict: "Verdict",
        source: str,
    ) -> list[HallucinationTag]:
        """Return the list of hallucination types present in this claim.

        Args:
            claim: The atomic factual statement.
            verdict: NLI verdict against the source (ENTAIL/CONTRADICT/NEUTRAL).
            source: The grounding document.

        Returns:
            List of HallucinationTag. Empty list means no hallucination
            (claim is grounded). Order is not significant.
        """
        # Fast path: a claim that entails the source has no hallucination.
        if verdict.value == "ENTAIL":
            return []

        prompt = CLASSIFIER_PROMPT_TEMPLATE.format(
            source=source,
            claim=claim,
            verdict=verdict.value,
        )

        raw = self._llm.generate(prompt)
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
        """Parse the JSON response into HallucinationTag objects.

        Robust to common LLM output quirks: markdown code fences, leading
        whitespace, trailing commentary.
        """
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
                continue  # Unknown type from the LLM, drop silently.
            if hh_type in seen:
                continue  # De-dupe if LLM repeats a type.
            seen.add(hh_type)
            explanation = str(item.get("explanation", "")).strip()
            # Cap explanation length to keep UI tidy.
            if len(explanation) > 200:
                explanation = explanation[:200].rstrip() + "..."
            tags.append(HallucinationTag(type=hh_type, explanation=explanation))

        return tags

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove ```json ... ``` fences if the LLM wrapped its output."""
        # Match opening fence, optional language tag, content, closing fence.
        m = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
        if m:
            return m.group(1)
        return text
'@ | Set-Content -Path .\src\hallucination_hunter\taxonomy.py -Encoding UTF8