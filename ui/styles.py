"""
Custom CSS theming for Hallucination Hunter.

Design tokens (per project spec):
    Background:    #0E1117   Card:          #1E1E1E
    Accent:        #00D9FF   (cyan, buttons + badges)
    PASS:          #00C853   WARNING:       #FFD600    FAIL:          #FF3D00
    Typography:    Inter
    Border radius: 8px       Transitions:   0.2s ease

Exposes a single function — `load_custom_css()` — that injects the stylesheet
via `st.markdown(..., unsafe_allow_html=True)`. Call once per page render,
after `st.set_page_config()`.
"""
from __future__ import annotations

import streamlit as st


_CSS = """
<style>
/* ---------- Font import ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ---------- Design tokens ---------- */
:root {
    --hh-bg:           #0E1117;
    --hh-bg-elev:      #16191F;
    --hh-card:         #1E1E1E;
    --hh-card-hover:   #25262C;
    --hh-border:       #2A2D35;
    --hh-border-soft:  #232630;

    --hh-text:         #E6E8EC;
    --hh-text-mute:    #9AA0AC;
    --hh-text-dim:     #6B7280;

    --hh-accent:       #00D9FF;
    --hh-accent-hi:    #4DE7FF;
    --hh-accent-lo:    #009DBA;

    --hh-pass:         #00C853;
    --hh-warn:         #FFD600;
    --hh-fail:         #FF3D00;

    --hh-radius:       8px;
    --hh-radius-lg:    12px;
    --hh-shadow:       0 4px 12px rgba(0,0,0,0.35);
    --hh-shadow-glow:  0 0 0 1px rgba(0,217,255,0.18), 0 6px 20px rgba(0,217,255,0.12);
    --hh-trans:        0.2s ease;

    --hh-font:         'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --hh-font-mono:    'JetBrains Mono', 'SF Mono', Consolas, monospace;
}

/* ---------- Global app surface ---------- */
.stApp {
    background: var(--hh-bg);
    color: var(--hh-text);
    font-family: var(--hh-font);
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 1100px;
}

/* Body text */
.stApp, .stApp p, .stApp li, .stApp span, .stApp div {
    font-family: var(--hh-font);
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: var(--hh-bg-elev);
    border-right: 1px solid var(--hh-border);
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

.hh-sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0 0.5rem 1rem 0.5rem;
}
.hh-sidebar-logo {
    width: 40px;
    height: 40px;
    border-radius: var(--hh-radius);
    background: linear-gradient(135deg, var(--hh-accent), var(--hh-accent-lo));
    color: #0E1117;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 1rem;
    letter-spacing: 0.02em;
    box-shadow: var(--hh-shadow);
}
.hh-sidebar-title {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--hh-text);
    line-height: 1.1;
}
.hh-sidebar-sub {
    font-size: 0.72rem;
    color: var(--hh-text-mute);
    margin-top: 0.15rem;
    letter-spacing: 0.02em;
}
.hh-sidebar-divider {
    height: 1px;
    background: var(--hh-border);
    margin: 0.5rem 0 1rem 0;
}
.hh-sidebar-foot {
    font-size: 0.7rem;
    color: var(--hh-text-dim);
    line-height: 1.5;
    padding: 0 0.5rem;
}

/* Sidebar radio */
[data-testid="stSidebar"] [role="radiogroup"] label {
    background: transparent;
    border-radius: var(--hh-radius);
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.25rem;
    transition: background var(--hh-trans), color var(--hh-trans);
    cursor: pointer;
    color: var(--hh-text-mute);
    font-weight: 500;
    font-size: 0.9rem;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: var(--hh-card-hover);
    color: var(--hh-text);
}

/* ---------- Page heads ---------- */
.hh-page-head {
    margin-bottom: 1.5rem;
}
.hh-page-title {
    font-family: var(--hh-font);
    font-weight: 700;
    font-size: 1.85rem;
    letter-spacing: -0.01em;
    color: var(--hh-text);
    margin: 0 0 0.4rem 0;
}
.hh-page-sub {
    color: var(--hh-text-mute);
    font-size: 0.95rem;
    line-height: 1.5;
    margin: 0;
    max-width: 720px;
}

/* Hero (About page) */
.hh-hero {
    background: linear-gradient(135deg, rgba(0,217,255,0.06), rgba(0,157,186,0.02));
    border: 1px solid var(--hh-border);
    border-radius: var(--hh-radius-lg);
    padding: 2rem 2rem 1.75rem;
    margin-bottom: 1.5rem;
}
.hh-hero-eyebrow {
    color: var(--hh-accent);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.hh-hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: var(--hh-text);
    letter-spacing: -0.02em;
    margin: 0 0 0.75rem 0;
    line-height: 1.05;
}
.hh-hero-lede {
    color: var(--hh-text-mute);
    font-size: 1.05rem;
    line-height: 1.55;
    max-width: 720px;
    margin: 0;
}
.hh-hero-lede em {
    color: var(--hh-accent-hi);
    font-style: normal;
    font-weight: 600;
}

/* ---------- Section heads ---------- */
.hh-section-head {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    margin: 0 0 1rem 0;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--hh-border-soft);
}
.hh-section-num {
    width: 26px;
    height: 26px;
    border-radius: 6px;
    background: var(--hh-accent);
    color: #0E1117;
    font-weight: 700;
    font-size: 0.85rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}
.hh-section-title {
    color: var(--hh-text);
    font-weight: 600;
    font-size: 1.05rem;
    letter-spacing: -0.005em;
}
.hh-section-tag {
    margin-left: auto;
    font-size: 0.72rem;
    color: var(--hh-text-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 500;
}
.hh-section-gap {
    height: 1.5rem;
}

/* H2 / H3 */
.hh-h2 {
    color: var(--hh-text);
    font-size: 1.35rem;
    font-weight: 700;
    margin: 2rem 0 0.75rem 0;
    letter-spacing: -0.01em;
}
.hh-h3 {
    color: var(--hh-text);
    font-size: 1.1rem;
    font-weight: 600;
    margin: 1.5rem 0 0.75rem 0;
}
.hh-prose {
    color: var(--hh-text-mute);
    line-height: 1.6;
    font-size: 0.95rem;
    max-width: 760px;
}
.hh-prose code {
    background: var(--hh-bg-elev);
    border: 1px solid var(--hh-border);
    border-radius: 4px;
    padding: 0.05rem 0.35rem;
    font-family: var(--hh-font-mono);
    font-size: 0.85em;
    color: var(--hh-accent-hi);
}

/* ---------- Inputs ---------- */
.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div {
    background: var(--hh-bg-elev) !important;
    border: 1px solid var(--hh-border) !important;
    border-radius: var(--hh-radius) !important;
    color: var(--hh-text) !important;
    font-family: var(--hh-font) !important;
    transition: border-color var(--hh-trans), box-shadow var(--hh-trans);
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--hh-accent) !important;
    box-shadow: 0 0 0 3px rgba(0, 217, 255, 0.15) !important;
    outline: none !important;
}
.stTextInput label,
.stTextArea label,
.stSelectbox label {
    color: var(--hh-text) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    margin-bottom: 0.3rem !important;
}

/* ---------- Buttons ---------- */
.stButton > button {
    background: var(--hh-card);
    color: var(--hh-text);
    border: 1px solid var(--hh-border);
    border-radius: var(--hh-radius);
    padding: 0.55rem 1.1rem;
    font-family: var(--hh-font);
    font-weight: 600;
    font-size: 0.9rem;
    transition: all var(--hh-trans);
    cursor: pointer;
}
.stButton > button:hover {
    background: var(--hh-card-hover);
    border-color: var(--hh-accent);
    color: var(--hh-accent-hi);
    transform: translateY(-1px);
}
.stButton > button:active {
    transform: translateY(0);
}
.stButton > button[kind="primary"] {
    background: var(--hh-accent);
    color: #0E1117;
    border-color: var(--hh-accent);
}
.stButton > button[kind="primary"]:hover {
    background: var(--hh-accent-hi);
    border-color: var(--hh-accent-hi);
    color: #0E1117;
    box-shadow: var(--hh-shadow-glow);
}

/* ---------- Readiness indicator ---------- */
.hh-ready {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.5rem 0.85rem;
    border-radius: var(--hh-radius);
    font-size: 0.85rem;
    font-weight: 500;
    margin-top: 0.5rem;
    transition: all var(--hh-trans);
}
.hh-ready-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.hh-ready-ok {
    background: rgba(0, 200, 83, 0.10);
    border: 1px solid rgba(0, 200, 83, 0.35);
    color: var(--hh-pass);
}
.hh-ready-ok .hh-ready-dot {
    background: var(--hh-pass);
    box-shadow: 0 0 8px rgba(0, 200, 83, 0.6);
}
.hh-ready-pending {
    background: rgba(255, 214, 0, 0.06);
    border: 1px solid rgba(255, 214, 0, 0.25);
    color: var(--hh-warn);
}
.hh-ready-pending .hh-ready-dot {
    background: var(--hh-warn);
}

/* ---------- Badges (About page) ---------- */
.hh-badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}
.hh-badge {
    display: inline-flex;
    overflow: hidden;
    border-radius: var(--hh-radius);
    border: 1px solid var(--hh-border);
    font-size: 0.78rem;
    font-family: var(--hh-font-mono);
}
.hh-badge-k {
    background: var(--hh-bg-elev);
    color: var(--hh-text-mute);
    padding: 0.3rem 0.6rem;
    border-right: 1px solid var(--hh-border);
}
.hh-badge-v {
    background: var(--hh-card);
    color: var(--hh-accent);
    padding: 0.3rem 0.6rem;
    font-weight: 600;
}

/* ---------- Triad cards ---------- */
.hh-triad-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1rem;
    margin: 1rem 0 1.5rem 0;
}
.hh-triad-card {
    background: var(--hh-card);
    border: 1px solid var(--hh-border);
    border-radius: var(--hh-radius-lg);
    padding: 1.25rem;
    transition: border-color var(--hh-trans), transform var(--hh-trans);
}
.hh-triad-card:hover {
    border-color: var(--hh-accent);
    transform: translateY(-2px);
}
.hh-triad-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
}
.hh-triad-icon {
    font-size: 1.5rem;
    color: var(--hh-accent);
    font-weight: 700;
}
.hh-triad-stage {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--hh-text-dim);
    background: var(--hh-bg-elev);
    padding: 0.2rem 0.55rem;
    border-radius: 4px;
}
.hh-triad-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--hh-text);
    margin-bottom: 0.4rem;
}
.hh-triad-body {
    color: var(--hh-text-mute);
    font-size: 0.88rem;
    line-height: 1.55;
}

/* ---------- Threshold blocks ---------- */
.hh-thresh-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.85rem;
    margin: 0.75rem 0 1.5rem 0;
}
.hh-thresh {
    background: var(--hh-card);
    border-radius: var(--hh-radius-lg);
    padding: 1.1rem 1.25rem;
    border: 1px solid var(--hh-border);
    border-left-width: 4px;
}
.hh-thresh-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}
.hh-thresh-range {
    font-family: var(--hh-font-mono);
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}
.hh-thresh-note {
    font-size: 0.82rem;
    color: var(--hh-text-mute);
    line-height: 1.5;
}
.hh-thresh-pass { border-left-color: var(--hh-pass); }
.hh-thresh-pass .hh-thresh-label,
.hh-thresh-pass .hh-thresh-range { color: var(--hh-pass); }
.hh-thresh-warn { border-left-color: var(--hh-warn); }
.hh-thresh-warn .hh-thresh-label,
.hh-thresh-warn .hh-thresh-range { color: var(--hh-warn); }
.hh-thresh-fail { border-left-color: var(--hh-fail); }
.hh-thresh-fail .hh-thresh-label,
.hh-thresh-fail .hh-thresh-range { color: var(--hh-fail); }

/* ---------- Example steps ---------- */
.hh-example {
    background: var(--hh-card);
    border: 1px solid var(--hh-border);
    border-radius: var(--hh-radius-lg);
    padding: 1.5rem;
    margin: 0.75rem 0 1.5rem 0;
}
.hh-example-step {
    display: flex;
    gap: 1rem;
    padding: 0.85rem 0;
    border-bottom: 1px solid var(--hh-border-soft);
}
.hh-example-step:last-child {
    border-bottom: none;
    padding-bottom: 0;
}
.hh-example-step:first-child {
    padding-top: 0;
}
.hh-step-num {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--hh-bg-elev);
    border: 1px solid var(--hh-border);
    color: var(--hh-accent);
    font-family: var(--hh-font-mono);
    font-weight: 700;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.hh-step-body {
    color: var(--hh-text-mute);
    font-size: 0.92rem;
    line-height: 1.55;
    padding-top: 0.3rem;
}
.hh-step-body strong {
    color: var(--hh-text);
    font-weight: 600;
}
.hh-step-body code {
    background: var(--hh-bg-elev);
    border: 1px solid var(--hh-border);
    padding: 0.05rem 0.35rem;
    border-radius: 4px;
    font-family: var(--hh-font-mono);
    font-size: 0.82em;
    color: var(--hh-accent-hi);
}

/* ---------- Faithfulness gauge ---------- */
.hh-gauge-wrap {
    background: var(--hh-card);
    border: 1px solid var(--hh-border);
    border-radius: var(--hh-radius-lg);
    padding: 1.25rem 1.5rem;
}
.hh-gauge-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--hh-text-dim);
    margin-bottom: 0.4rem;
}
.hh-gauge-value {
    font-family: var(--hh-font-mono);
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 0.85rem;
}
.hh-gauge-track {
    position: relative;
    height: 10px;
    background: var(--hh-bg-elev);
    border-radius: 5px;
    overflow: visible;
    border: 1px solid var(--hh-border-soft);
}
.hh-gauge-fill {
    height: 100%;
    border-radius: 5px;
    transition: width 0.4s ease;
}
.hh-gauge-tick {
    position: absolute;
    top: -4px;
    width: 2px;
    height: 18px;
    background: var(--hh-text-dim);
    opacity: 0.5;
    transform: translateX(-1px);
}
.hh-gauge-scale {
    display: flex;
    justify-content: space-between;
    margin-top: 0.5rem;
    font-family: var(--hh-font-mono);
    font-size: 0.72rem;
    color: var(--hh-text-dim);
}
.hh-gauge-pass { color: var(--hh-pass); }
.hh-gauge-pass.hh-gauge-fill,
.hh-gauge-pass.hh-conf-fill { background: var(--hh-pass); }
.hh-gauge-warn { color: var(--hh-warn); }
.hh-gauge-warn.hh-gauge-fill,
.hh-gauge-warn.hh-conf-fill { background: var(--hh-warn); }
.hh-gauge-fail { color: var(--hh-fail); }
.hh-gauge-fail.hh-gauge-fill,
.hh-gauge-fail.hh-conf-fill { background: var(--hh-fail); }

/* ---------- Status badge ---------- */
.hh-status-badge {
    display: inline-block;
    padding: 0.55rem 1.1rem;
    border-radius: var(--hh-radius);
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    text-align: center;
    margin-bottom: 0.85rem;
}
.hh-status-pass {
    background: rgba(0, 200, 83, 0.12);
    color: var(--hh-pass);
    border: 1px solid rgba(0, 200, 83, 0.4);
}
.hh-status-warn {
    background: rgba(255, 214, 0, 0.12);
    color: var(--hh-warn);
    border: 1px solid rgba(255, 214, 0, 0.4);
}
.hh-status-fail {
    background: rgba(255, 61, 0, 0.12);
    color: var(--hh-fail);
    border: 1px solid rgba(255, 61, 0, 0.4);
}

/* ---------- Verdict count chips ---------- */
.hh-count-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    margin-top: 0.5rem;
}
.hh-count-chip {
    background: var(--hh-card);
    border: 1px solid var(--hh-border);
    border-radius: var(--hh-radius);
    padding: 0.55rem 0.7rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.hh-count-icon {
    font-size: 1rem;
    font-weight: 700;
    width: 22px;
    text-align: center;
}
.hh-count-num {
    font-family: var(--hh-font-mono);
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--hh-text);
}
.hh-count-lbl {
    font-size: 0.72rem;
    color: var(--hh-text-mute);
    margin-left: auto;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ---------- Claim cards ---------- */
.hh-claim-card {
    background: var(--hh-bg-elev);
    border-radius: var(--hh-radius);
    padding: 0.85rem 1rem 1rem;
    margin-bottom: 0.5rem;
}
.hh-claim-text {
    color: var(--hh-text);
    font-size: 0.95rem;
    line-height: 1.55;
    margin-bottom: 0.85rem;
}
.hh-claim-meta {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
}
.hh-claim-conf-label {
    margin-left: auto;
    font-size: 0.72rem;
    color: var(--hh-text-dim);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 500;
}
.hh-conf-bar {
    background: var(--hh-bg);
    border: 1px solid var(--hh-border-soft);
    border-radius: 5px;
    height: 6px;
    overflow: hidden;
    margin-bottom: 0.3rem;
}
.hh-conf-fill {
    height: 100%;
    transition: width 0.4s ease;
}
.hh-conf-value {
    font-family: var(--hh-font-mono);
    font-size: 0.78rem;
    color: var(--hh-text-mute);
    text-align: right;
}

/* Verdict badges */
.hh-verdict-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.3rem 0.6rem;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.hh-verdict-icon {
    font-size: 0.9rem;
    line-height: 1;
}
.hh-verdict-supported {
    background: rgba(0, 200, 83, 0.12);
    color: var(--hh-pass);
    border: 1px solid rgba(0, 200, 83, 0.4);
}
.hh-verdict-supported.hh-conf-fill,
.hh-verdict-supported.hh-count-chip { background: rgba(0, 200, 83, 0.06); }
.hh-verdict-supported.hh-conf-fill { background: var(--hh-pass); }
.hh-verdict-contradicted {
    background: rgba(255, 61, 0, 0.12);
    color: var(--hh-fail);
    border: 1px solid rgba(255, 61, 0, 0.4);
}
.hh-verdict-contradicted.hh-conf-fill { background: var(--hh-fail); }
.hh-verdict-notfound {
    background: rgba(255, 214, 0, 0.12);
    color: var(--hh-warn);
    border: 1px solid rgba(255, 214, 0, 0.4);
}
.hh-verdict-notfound.hh-conf-fill { background: var(--hh-warn); }
.hh-verdict-neutral {
    background: rgba(154, 160, 172, 0.10);
    color: var(--hh-text-mute);
    border: 1px solid var(--hh-border);
}
.hh-verdict-neutral.hh-conf-fill { background: var(--hh-text-mute); }

/* ---------- Evidence ---------- */
.hh-evidence {
    margin-top: 0.85rem;
    padding-top: 0.85rem;
    border-top: 1px solid var(--hh-border-soft);
}
.hh-evidence-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--hh-text-dim);
    margin-bottom: 0.45rem;
}
.hh-evidence-quote {
    background: var(--hh-bg);
    border-left: 3px solid var(--hh-accent);
    padding: 0.7rem 0.95rem;
    margin: 0;
    color: var(--hh-text-mute);
    font-size: 0.88rem;
    line-height: 1.5;
    border-radius: 0 var(--hh-radius) var(--hh-radius) 0;
    font-style: italic;
}
.hh-evidence-empty .hh-evidence-label {
    color: var(--hh-text-dim);
    font-style: italic;
    text-transform: none;
    letter-spacing: 0;
}

/* ---------- Streamlit chrome cleanup ---------- */
[data-testid="stToolbar"], footer { display: none !important; }
#MainMenu { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* Expander styling */
[data-testid="stExpander"] {
    background: var(--hh-card);
    border: 1px solid var(--hh-border);
    border-radius: var(--hh-radius);
    margin-bottom: 0.5rem;
    transition: border-color var(--hh-trans);
}
[data-testid="stExpander"]:hover {
    border-color: var(--hh-border);
}
[data-testid="stExpander"] summary {
    color: var(--hh-text);
    font-weight: 500;
    padding: 0.75rem 1rem;
}

/* Progress bar */
.stProgress > div > div > div > div {
    background: var(--hh-accent) !important;
}
.stProgress > div > div > div {
    background: var(--hh-bg-elev) !important;
}

/* Spinner */
.stSpinner > div {
    border-top-color: var(--hh-accent) !important;
}

/* Alerts */
.stAlert {
    border-radius: var(--hh-radius);
    border-left-width: 3px;
}

/* ---------- Error card (Chunk C1) ---------- */
.hh-error-card {
    background: var(--hh-card);
    border: 1px solid var(--hh-fail);
    border-radius: var(--hh-radius-lg);
    padding: 1.25rem 1.5rem;
    margin-top: 0.5rem;
}
.hh-error-head {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
}
.hh-error-code {
    font-family: var(--hh-font-mono);
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--hh-fail);
    background: rgba(255, 61, 0, 0.10);
    padding: 0.25rem 0.6rem;
    border-radius: var(--hh-radius);
    border: 1px solid rgba(255, 61, 0, 0.35);
}
.hh-error-cat {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--hh-text-mute);
    border: 1px solid var(--hh-border);
    padding: 0.2rem 0.5rem;
    border-radius: var(--hh-radius);
}
.hh-error-retry {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 0.2rem 0.5rem;
    border-radius: var(--hh-radius);
}
.hh-error-retry-yes {
    color: var(--hh-pass);
    background: rgba(0, 200, 83, 0.10);
    border: 1px solid rgba(0, 200, 83, 0.35);
}
.hh-error-retry-no {
    color: var(--hh-warn);
    background: rgba(255, 214, 0, 0.10);
    border: 1px solid rgba(255, 214, 0, 0.35);
}
.hh-error-msg {
    color: var(--hh-text);
    font-size: 1rem;
    line-height: 1.5;
    margin-bottom: 1rem;
}
.hh-error-sug {
    background: var(--hh-bg-elev);
    border-left: 3px solid var(--hh-accent);
    padding: 0.75rem 1rem;
    border-radius: 0 var(--hh-radius) var(--hh-radius) 0;
}
.hh-error-sug-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--hh-accent);
    margin-bottom: 0.25rem;
}

/* ---------- Char counter (Chunk C1) ---------- */
.hh-char-counter {
    text-align: right;
    font-family: var(--hh-font-mono);
    font-size: 0.78rem;
    margin-top: -0.5rem;
    margin-bottom: 0.75rem;
    transition: color var(--hh-trans);
}
.hh-counter-ok    { color: var(--hh-text-dim); }
.hh-counter-soft  { color: var(--hh-warn); }
.hh-counter-warn  { color: var(--hh-fail); font-weight: 600; }

</style>
"""


def load_custom_css() -> None:
    """Inject the Hallucination Hunter custom stylesheet.

    Call once per page render, after ``st.set_page_config()``. Streamlit
    deduplicates identical markdown blocks so calling on every rerun is
    safe.
    """
    st.markdown(_CSS, unsafe_allow_html=True)