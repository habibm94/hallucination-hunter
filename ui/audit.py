"""Audit page UI for Hallucination Hunter."""

from __future__ import annotations

from typing import Any

import streamlit as st

from hallucination_hunter.errors import (
    MAX_ANSWER_CHARS,
    MAX_QUESTION_CHARS,
    MAX_SOURCE_CHARS,
    HallucinationHunterError,
    make_error,
)
from hallucination_hunter.models import AuditStatus
from hallucination_hunter.pipeline import HallucinationHunter
from hallucination_hunter.providers import (
    PROVIDER_MODELS,
    PROVIDER_STATUS,
    SUPPORTED_PROVIDERS,
    create_provider,
)


_VERDICT_STYLES: dict[str, dict[str, str]] = {
    "ENTAIL": {"cls": "hh-verdict-supported", "icon": "v", "label": "SUPPORTED"},
    "CONTRADICT": {"cls": "hh-verdict-contradicted", "icon": "x", "label": "CONTRADICTED"},
    "NEUTRAL": {"cls": "hh-verdict-notfound", "icon": "?", "label": "NOT FOUND"},
}

_STATUS_STYLES: dict[str, dict[str, str]] = {
    "PASS": {"cls": "hh-status-pass", "label": "PASS"},
    "WARNING": {"cls": "hh-status-warn", "label": "WARNING"},
    "FAIL": {"cls": "hh-status-fail", "label": "FAIL"},
}


def _session_key(provider: str) -> str:
    return f"{provider}_key"


def _get_status_label(status: Any) -> str:
    if isinstance(status, AuditStatus):
        return status.name
    if hasattr(status, "name"):
        return str(status.name)
    return str(status).upper()


def _score_color_class(score: float) -> str:
    if score >= 0.85:
        return "hh-gauge-pass"
    if score >= 0.50:
        return "hh-gauge-warn"
    return "hh-gauge-fail"


def _safe_get(obj: Any, attr: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)


def _html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _render_char_counter(text: str, limit: int) -> None:
    """Render a small character counter under a text field."""
    used = len(text or "")
    pct = (used / limit) if limit else 0
    if pct >= 0.95:
        cls = "hh-counter-warn"
    elif pct >= 0.75:
        cls = "hh-counter-soft"
    else:
        cls = "hh-counter-ok"
    st.markdown(
        f"<div class='hh-char-counter {cls}'>"
        f"{used:,} / {limit:,} chars</div>",
        unsafe_allow_html=True,
    )


def _render_provider_setup() -> tuple[str | None, str | None, str | None]:
    """Render provider/model/key controls. Reactive readiness indicator."""
    st.markdown(
        "<div class='hh-section-head'>"
        "<span class='hh-section-num'>A</span>"
        "<span class='hh-section-title'>Provider Setup</span>"
        "<span class='hh-section-tag'>BYOK · session-only</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not SUPPORTED_PROVIDERS:
        st.error("No providers are registered. Check your providers package.")
        return None, None, None

    col_provider, col_model = st.columns([1, 1])

    with col_provider:
        provider = st.selectbox(
            "Provider",
            options=SUPPORTED_PROVIDERS,
            key="hh_provider_select",
            help="Choose which LLM provider to use for claim extraction and NLI.",
        )

    provider_status_raw = (
        PROVIDER_STATUS.get(provider, "available") if PROVIDER_STATUS else "available"
    )
    status_ok = str(provider_status_raw).lower() == "available"
    if not status_ok:
        st.warning(
            f"{provider} is currently unavailable (status: {provider_status_raw}). "
            "Pick a different provider above."
        )
        return provider, None, None

    available_models_dict = PROVIDER_MODELS.get(provider, {})
    available_model_ids = (
        list(available_models_dict.values()) if available_models_dict else []
    )

    with col_model:
        if not available_model_ids:
            st.warning(f"No models registered for {provider}.")
            model = None
        else:
            model = st.selectbox(
                "Model",
                options=available_model_ids,
                key=f"hh_model_select_{provider}",
                help="Model used for claim extraction and NLI verification.",
            )

    apikey_widget_key = f"hh_apikey_input_{provider}"
    api_key = st.text_input(
        f"{provider} API Key",
        type="password",
        key=apikey_widget_key,
        placeholder="sk-..." if provider.lower() == "openai" else "Paste your API key",
        help=(
            "Stored in session state only. Never written to disk. "
            "Cleared when the tab closes."
        ),
    )

    if api_key:
        st.session_state[_session_key(provider)] = api_key
    else:
        st.session_state.pop(_session_key(provider), None)

    has_key = bool(api_key)
    if has_key and model:
        st.markdown(
            "<div class='hh-ready hh-ready-ok'>"
            "<span class='hh-ready-dot'></span>"
            f"<span>Ready · {provider} / {model}</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        missing = []
        if not has_key:
            missing.append("API key")
        if not model:
            missing.append("model")
        missing_text = ", ".join(missing)
        st.markdown(
            "<div class='hh-ready hh-ready-pending'>"
            "<span class='hh-ready-dot'></span>"
            f"<span>Awaiting: {missing_text}</span>"
            "</div>",
            unsafe_allow_html=True,
        )

    return provider, model, api_key if api_key else None


def _render_input_fields() -> tuple[str, str, str]:
    """Render source/question/answer inputs with visible char counters."""
    st.markdown(
        "<div class='hh-section-head'>"
        "<span class='hh-section-num'>B</span>"
        "<span class='hh-section-title'>Audit Inputs</span>"
        "<span class='hh-section-tag'>source · question · answer</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    source_label = f"Source Context  ·  max {MAX_SOURCE_CHARS:,} chars"
    source = st.text_area(
        source_label,
        placeholder=(
            "Paste knowledge base text, retrieved documents, or any "
            "grounding material the answer should be faithful to..."
        ),
        height=220,
        max_chars=MAX_SOURCE_CHARS,
        key="hh_input_source",
        help=(
            "The ground truth. Every claim in the answer will be checked "
            f"against this. Limit: {MAX_SOURCE_CHARS:,} characters."
        ),
    )
    _render_char_counter(source, MAX_SOURCE_CHARS)

    question_label = f"User Question  ·  max {MAX_QUESTION_CHARS:,} chars"
    question = st.text_area(
        question_label,
        placeholder="What was asked of the LLM?",
        height=80,
        max_chars=MAX_QUESTION_CHARS,
        key="hh_input_question",
        help=f"The question posed to the LLM. Limit: {MAX_QUESTION_CHARS:,} characters.",
    )
    _render_char_counter(question, MAX_QUESTION_CHARS)

    answer_label = f"LLM Answer  ·  max {MAX_ANSWER_CHARS:,} chars"
    answer = st.text_area(
        answer_label,
        placeholder="Paste the model's response here...",
        height=180,
        max_chars=MAX_ANSWER_CHARS,
        key="hh_input_answer",
        help=(
            "The LLM-generated response to audit. "
            f"Limit: {MAX_ANSWER_CHARS:,} characters."
        ),
    )
    _render_char_counter(answer, MAX_ANSWER_CHARS)

    return source, question, answer


def _render_execution(
    provider: str | None,
    model: str | None,
    api_key: str | None,
    source: str,
    question: str,
    answer: str,
) -> None:
    """Run Audit / Clear buttons and orchestration."""
    st.markdown(
        "<div class='hh-section-head'>"
        "<span class='hh-section-num'>C</span>"
        "<span class='hh-section-title'>Run Audit</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    col_run, col_clear, _ = st.columns([1, 1, 3])
    with col_run:
        run_clicked = st.button(
            "Run Audit",
            type="primary",
            use_container_width=True,
            key="hh_run_button",
        )
    with col_clear:
        clear_clicked = st.button(
            "Clear",
            use_container_width=True,
            key="hh_clear_button",
            help="Clear the last audit result.",
        )

    if clear_clicked:
        st.session_state.pop("last_report", None)
        st.session_state.pop("last_error", None)
        st.rerun()

    if not run_clicked:
        return

    if not provider:
        st.warning("Pick a provider in Section A.")
        return
    if not model:
        st.warning("Pick a model in Section A.")
        return
    if not api_key:
        st.warning("API key is required. Enter it in Section A.")
        return

    progress_slot = st.empty()
    progress_bar = progress_slot.progress(0, text="Starting audit...")

    stage_progress = {
        "extracting claims": 0.20,
        "verifying": 0.55,
        "calculating metrics": 0.90,
    }

    def _on_progress(msg: str) -> None:
        for keyword, pct in stage_progress.items():
            if msg.lower().startswith(keyword):
                progress_bar.progress(pct, text=msg)
                return
        progress_bar.progress(0.10, text=msg)

    try:
        provider_instance = create_provider(provider, api_key, model)
        hunter = HallucinationHunter(
            provider=provider,
            model=model,
            _provider_instance=provider_instance,
        )
        report = hunter.audit(
            source=source,
            question=question,
            answer=answer,
            progress_callback=_on_progress,
        )
        progress_bar.progress(1.0, text="Done.")
        progress_slot.empty()
        st.session_state["last_report"] = report
        st.session_state.pop("last_error", None)

    except HallucinationHunterError as e:
        progress_slot.empty()
        st.session_state["last_error"] = e.detail
        st.session_state.pop("last_report", None)

    except Exception as e:
        progress_slot.empty()
        st.session_state["last_error"] = make_error(
            "HH-INTERNAL-001",
            context={"exc_type": type(e).__name__, "underlying": str(e)},
        )
        st.session_state.pop("last_report", None)


def _render_gauge(score: float) -> None:
    pct = max(0.0, min(1.0, float(score))) * 100
    color_cls = _score_color_class(score)
    st.markdown(
        f"<div class='hh-gauge-wrap'>"
        f"<div class='hh-gauge-label'>Faithfulness Score</div>"
        f"<div class='hh-gauge-value {color_cls}'>{score:.2f}</div>"
        f"<div class='hh-gauge-track'>"
        f"<div class='hh-gauge-fill {color_cls}' style='width: {pct:.1f}%;'></div>"
        f"<div class='hh-gauge-tick' style='left: 50%;'></div>"
        f"<div class='hh-gauge-tick' style='left: 85%;'></div>"
        f"</div>"
        f"<div class='hh-gauge-scale'>"
        f"<span>0.00</span><span>0.50</span><span>0.85</span><span>1.00</span>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_status_badge(status_label: str) -> None:
    style = _STATUS_STYLES.get(status_label, _STATUS_STYLES["WARNING"])
    badge_cls = style["cls"]
    badge_label = style["label"]
    st.markdown(
        f"<div class='hh-status-badge {badge_cls}'>{badge_label}</div>",
        unsafe_allow_html=True,
    )


def _render_claim_card(claim: Any, idx: int) -> None:
    text = _safe_get(claim, "claim", "") or _safe_get(claim, "text", "")
    verdict_raw = _safe_get(claim, "verdict", "NEUTRAL")
    verdict = (
        verdict_raw.value
        if hasattr(verdict_raw, "value")
        else str(verdict_raw).upper()
    )
    score = float(_safe_get(claim, "score", 0.0) or 0.0)
    evidence = (
        _safe_get(claim, "source_evidence", "")
        or _safe_get(claim, "evidence", "")
        or ""
    )

    style = _VERDICT_STYLES.get(verdict, _VERDICT_STYLES["NEUTRAL"])
    pct = max(0.0, min(1.0, score)) * 100
    s_cls = style["cls"]
    s_icon = style["icon"]
    s_label = style["label"]

    header = f"Claim {idx + 1}  ·  {s_label}"
    with st.expander(header, expanded=(verdict in ("CONTRADICT", "NEUTRAL"))):
        st.markdown(
            f"<div class='hh-claim-card'>"
            f"<div class='hh-claim-text'>{_html_escape(text)}</div>"
            f"<div class='hh-claim-meta'>"
            f"<span class='hh-verdict-badge {s_cls}'>"
            f"<span class='hh-verdict-icon'>{s_icon}</span>"
            f"<span>{s_label}</span>"
            f"</span>"
            f"<span class='hh-claim-conf-label'>NLI score</span>"
            f"</div>"
            f"<div class='hh-conf-bar'>"
            f"<div class='hh-conf-fill {s_cls}' style='width: {pct:.1f}%;'></div>"
            f"</div>"
            f"<div class='hh-conf-value'>{score:.2f}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if evidence:
            st.markdown(
                f"<div class='hh-evidence'>"
                f"<div class='hh-evidence-label'>Matching evidence</div>"
                f"<blockquote class='hh-evidence-quote'>{_html_escape(evidence)}</blockquote>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='hh-evidence hh-evidence-empty'>"
                "<div class='hh-evidence-label'>No matching evidence in source.</div>"
                "</div>",
                unsafe_allow_html=True,
            )


def _render_error(detail: Any) -> None:
    st.markdown(
        "<div class='hh-section-head'>"
        "<span class='hh-section-num'>D</span>"
        "<span class='hh-section-title'>Audit Failed</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    code = _safe_get(detail, "code", "HH-INTERNAL-001")
    category = _safe_get(detail, "category", "INTERNAL")
    category_label = (
        category.value if hasattr(category, "value") else str(category)
    )
    message = _safe_get(detail, "message", "Unknown error.")
    suggestion = _safe_get(detail, "suggestion", "")
    retry_safe = bool(_safe_get(detail, "retry_safe", False))

    retry_chip = (
        "<span class='hh-error-retry hh-error-retry-yes'>retry-safe</span>"
        if retry_safe
        else "<span class='hh-error-retry hh-error-retry-no'>not retry-safe</span>"
    )

    st.markdown(
        f"<div class='hh-error-card'>"
        f"<div class='hh-error-head'>"
        f"<span class='hh-error-code'>{_html_escape(code)}</span>"
        f"<span class='hh-error-cat'>{_html_escape(category_label)}</span>"
        f"{retry_chip}"
        f"</div>"
        f"<div class='hh-error-msg'>{_html_escape(message)}</div>"
        f"<div class='hh-error-sug'>"
        f"<div class='hh-error-sug-label'>Suggestion</div>"
        f"<div>{_html_escape(suggestion)}</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _build_count_chip(verdict_key: str, count: int) -> str:
    vstyle = _VERDICT_STYLES[verdict_key]
    v_cls = vstyle["cls"]
    v_icon = vstyle["icon"]
    v_label = vstyle["label"]
    return (
        f"<div class='hh-count-chip {v_cls}'>"
        f"<span class='hh-count-icon'>{v_icon}</span>"
        f"<span class='hh-count-num'>{count}</span>"
        f"<span class='hh-count-lbl'>{v_label}</span>"
        f"</div>"
    )


def _render_results() -> None:
    error = st.session_state.get("last_error")
    if error is not None:
        _render_error(error)
        return

    report = st.session_state.get("last_report")
    if report is None:
        return

    st.markdown(
        "<div class='hh-section-head'>"
        "<span class='hh-section-num'>D</span>"
        "<span class='hh-section-title'>Audit Report</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    score = float(_safe_get(report, "faithfulness_score", 0.0) or 0.0)
    status_label = _get_status_label(_safe_get(report, "status", "WARNING"))
    claims = _safe_get(report, "claims", []) or []

    col_gauge, col_meta = st.columns([2, 1])
    with col_gauge:
        _render_gauge(score)
    with col_meta:
        _render_status_badge(status_label)
        verdicts = []
        for c in claims:
            v = _safe_get(c, "verdict", "NEUTRAL")
            v = v.value if hasattr(v, "value") else str(v).upper()
            verdicts.append(v)
        counts = {
            "ENTAIL": verdicts.count("ENTAIL"),
            "CONTRADICT": verdicts.count("CONTRADICT"),
            "NEUTRAL": verdicts.count("NEUTRAL"),
        }
        chip_parts = [_build_count_chip(k, v) for k, v in counts.items()]
        chips_html = "".join(chip_parts)
        st.markdown(
            f"<div class='hh-count-grid'>{chips_html}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<h3 class='hh-h3'>Claims Breakdown</h3>", unsafe_allow_html=True)
    if not claims:
        st.info("No claims were extracted from the answer.")
        return

    for idx, claim in enumerate(claims):
        _render_claim_card(claim, idx)


def audit_ui() -> None:
    """Render the full Audit page."""
    st.markdown(
        "<div class='hh-page-head'>"
        "<h1 class='hh-page-title'>Audit an LLM Answer</h1>"
        "<p class='hh-page-sub'>"
        "Three inputs · one report. Extract atomic claims, verify each "
        "against the source via NLI, and surface every drift."
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    with st.container():
        provider, model, api_key = _render_provider_setup()

    st.markdown("<div class='hh-section-gap'></div>", unsafe_allow_html=True)

    with st.container():
        source, question, answer = _render_input_fields()

    st.markdown("<div class='hh-section-gap'></div>", unsafe_allow_html=True)

    with st.container():
        _render_execution(provider, model, api_key, source, question, answer)

    st.markdown("<div class='hh-section-gap'></div>", unsafe_allow_html=True)

    with st.container():
        _render_results()
