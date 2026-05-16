import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

"""
Hallucination Hunter — Streamlit entry point.

A local RAG evaluation tool implementing the RAG Triad framework
(Context Relevance · Faithfulness · Answer Relevance) for detecting
LLM hallucinations against a grounded source context.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from ui.audit import audit_ui
from ui.styles import load_custom_css


PAGE_AUDIT = "🎯 Audit"
PAGE_ABOUT = "ℹ️ About"


def _configure_page() -> None:
    """Configure global Streamlit page settings. Must run before any other st calls."""
    st.set_page_config(
        page_title="Hallucination Hunter",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def _render_sidebar() -> str:
    """Render the sidebar navigation and return the selected page label."""
    with st.sidebar:
        st.markdown(
            "<div class='hh-sidebar-brand'>"
            "<div class='hh-sidebar-logo'>HH</div>"
            "<div>"
            "<div class='hh-sidebar-title'>Hallucination Hunter</div>"
            "<div class='hh-sidebar-sub'>RAG Triad Evaluator</div>"
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='hh-sidebar-divider'></div>", unsafe_allow_html=True)

        page = st.radio(
            label="Navigation",
            options=[PAGE_AUDIT, PAGE_ABOUT],
            label_visibility="collapsed",
            key="hh_nav_page",
        )

        st.markdown("<div class='hh-sidebar-divider'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='hh-sidebar-foot'>"
            "BYOK · session-scoped<br>"
            "No keys written to disk"
            "</div>",
            unsafe_allow_html=True,
        )
    return page


def _render_about() -> None:
    """Render the About / project overview page."""
    st.markdown(
        "<div class='hh-hero'>"
        "<div class='hh-hero-eyebrow'>EvalOps · Local RAG Auditing</div>"
        "<h1 class='hh-hero-title'>Hallucination Hunter</h1>"
        "<p class='hh-hero-lede'>"
        "A grounded-evaluation tool that scores LLM answers against a source "
        "context using the RAG Triad — so you can see <em>where</em> a model "
        "drifted, not just <em>that</em> it did."
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    badges = [
        ("Python", "3.11+"),
        ("Streamlit", "Native"),
        ("Providers", "4"),
        ("BYOK", "Session-only"),
        ("License", "MIT"),
    ]
    badge_html = "".join(
        f"<span class='hh-badge'><span class='hh-badge-k'>{k}</span>"
        f"<span class='hh-badge-v'>{v}</span></span>"
        for k, v in badges
    )
    st.markdown(f"<div class='hh-badge-row'>{badge_html}</div>", unsafe_allow_html=True)

    st.markdown("<h2 class='hh-h2'>The RAG Triad</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='hh-prose'>"
        "Three complementary metrics that, together, locate the failure inside a "
        "RAG pipeline. Each one isolates a different stage — retrieval, generation, "
        "or alignment — so when something breaks, you know which lever to pull."
        "</p>",
        unsafe_allow_html=True,
    )

    triad = [
        {
            "icon": "①",
            "title": "Context Relevance",
            "stage": "Retrieval",
            "body": (
                "Did the retriever pull documents that actually address the question? "
                "Low scores point at chunking, embedding, or index quality — not the LLM."
            ),
        },
        {
            "icon": "②",
            "title": "Faithfulness",
            "stage": "Generation",
            "body": (
                "Is every claim in the answer supported by the retrieved context? "
                "This is the hallucination axis. Claims are extracted, then verified "
                "via NLI against the source."
            ),
        },
        {
            "icon": "③",
            "title": "Answer Relevance",
            "stage": "Alignment",
            "body": (
                "Does the answer actually address what was asked? A grounded answer "
                "to the wrong question still fails the user."
            ),
        },
    ]
    cards = "".join(
        f"<div class='hh-triad-card'>"
        f"<div class='hh-triad-head'>"
        f"<span class='hh-triad-icon'>{c['icon']}</span>"
        f"<span class='hh-triad-stage'>{c['stage']}</span>"
        f"</div>"
        f"<div class='hh-triad-title'>{c['title']}</div>"
        f"<div class='hh-triad-body'>{c['body']}</div>"
        f"</div>"
        for c in triad
    )
    st.markdown(f"<div class='hh-triad-grid'>{cards}</div>", unsafe_allow_html=True)

    st.markdown("<h2 class='hh-h2'>Faithfulness Thresholds</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hh-thresh-grid'>"
        "<div class='hh-thresh hh-thresh-pass'>"
        "<div class='hh-thresh-label'>PASS</div>"
        "<div class='hh-thresh-range'>≥ 0.85</div>"
        "<div class='hh-thresh-note'>Production-ready grounding. "
        "Almost every claim traces back to the source.</div>"
        "</div>"
        "<div class='hh-thresh hh-thresh-warn'>"
        "<div class='hh-thresh-label'>WARNING</div>"
        "<div class='hh-thresh-range'>0.50 – 0.84</div>"
        "<div class='hh-thresh-note'>Partial drift detected. "
        "Review unsupported claims before shipping.</div>"
        "</div>"
        "<div class='hh-thresh hh-thresh-fail'>"
        "<div class='hh-thresh-label'>FAIL</div>"
        "<div class='hh-thresh-range'>&lt; 0.50</div>"
        "<div class='hh-thresh-note'>Severe hallucination. "
        "More than half the claims are unsupported or contradicted.</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<h2 class='hh-h2'>Example Use Case</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hh-example'>"
        "<div class='hh-example-step'>"
        "<div class='hh-step-num'>01</div>"
        "<div class='hh-step-body'>"
        "<strong>Paste the source.</strong> A policy doc, a knowledge-base article, "
        "or any chunk a RAG system would retrieve."
        "</div>"
        "</div>"
        "<div class='hh-example-step'>"
        "<div class='hh-step-num'>02</div>"
        "<div class='hh-step-body'>"
        "<strong>Provide the question and the answer.</strong> The answer is whatever "
        "your model generated — paste it verbatim."
        "</div>"
        "</div>"
        "<div class='hh-example-step'>"
        "<div class='hh-step-num'>03</div>"
        "<div class='hh-step-body'>"
        "<strong>Run the audit.</strong> Hallucination Hunter extracts atomic claims, "
        "verifies each against the source via NLI, and returns a per-claim verdict "
        "plus an aggregate Faithfulness score."
        "</div>"
        "</div>"
        "<div class='hh-example-step'>"
        "<div class='hh-step-num'>04</div>"
        "<div class='hh-step-body'>"
        "<strong>Read the breakdown.</strong> Each claim is tagged "
        "<code>SUPPORTED</code>, <code>CONTRADICTED</code>, <code>NOT_FOUND</code>, "
        "or <code>NEUTRAL</code> — with the matching evidence snippet inline."
        "</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<h2 class='hh-h2'>Privacy Model</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p class='hh-prose'>"
        "API keys live in <code>st.session_state</code> for the duration of your "
        "browser session. Nothing is written to disk, and nothing leaves your machine "
        "except the calls you explicitly make to your chosen provider. Close the tab "
        "and the keys are gone."
        "</p>",
        unsafe_allow_html=True,
    )


def main() -> None:
    """Application entry point."""
    _configure_page()
    load_custom_css()
    page = _render_sidebar()

    if page == PAGE_AUDIT:
        audit_ui()
    else:
        _render_about()


if __name__ == "__main__":
    main()
