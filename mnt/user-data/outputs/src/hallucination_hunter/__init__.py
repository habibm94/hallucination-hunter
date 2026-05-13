"""Hallucination Hunter — automated faithfulness evaluation for LLM outputs.

Public API::

    from hallucination_hunter import HallucinationHunter, AuditReport

    hunter = HallucinationHunter()            # reads GEMINI_API_KEY from .env
    report = hunter.audit(source, question, answer)
    print(report.faithfulness_score)          # float in [0.0, 1.0]
    print(report.to_dict())                   # JSON-serialisable dict
"""

from hallucination_hunter.models import (
    AuditReport,
    AuditStatus,
    ClaimResult,
    Verdict,
)
from hallucination_hunter.pipeline import HallucinationHunter

__version__ = "0.1.0"
__author__ = "Habibullah Bin Mahmud"

__all__ = [
    "AuditReport",
    "AuditStatus",
    "ClaimResult",
    "HallucinationHunter",
    "Verdict",
    "__version__",
]
