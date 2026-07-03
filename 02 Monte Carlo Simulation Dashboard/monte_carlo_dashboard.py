import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import (
    compute_equity_curve,
    format_currency,
    format_pct,
    generate_demo_data,
    run_monte_carlo,
    validate_csv,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Monte Carlo · Nebula",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>
/* ── Root & background ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #060614;
    color: #c8c8e0;
    font-family: 'DM Sans', sans-serif;
}

/* ── FIX: Top white patch ── */
/* Give the header a dark background but keep its height so buttons stay accessible */
[data-testid="stHeader"] {
    background: #060614 !important;
    border-bottom: 1px solid rgba(100,120,255,0.08) !important;
}

/* ── FIX: Sidebar expand/collapse toggle ── */
/* The toggle lives INSIDE stHeader in modern Streamlit.
   Style it without touching position/layout so Streamlit keeps control. */

/* The wrapper div (contains the clickable area) */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    background: rgba(77,142,255,0.12) !important;
    border: 1px solid rgba(77,142,255,0.4) !important;
    border-radius: 8px !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 99999 !important;
    width: 40px !important;
    height: 40px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    background: rgba(77,142,255,0.25) !important;
    border-color: #4d8eff !important;
    box-shadow: 0 0 14px rgba(77,142,255,0.3) !important;
}

/* The actual button inside the wrapper */
[data-testid="collapsedControl"] button,
[data-testid="stSidebarCollapsedControl"] button {
    background: transparent !important;
    border: none !important;
    color: #a0b8ff !important;
    visibility: visible !important;
    opacity: 1 !important;
    width: 100% !important;
    height: 100% !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* ALL buttons that live in the header bar (covers any Streamlit version) */
[data-testid="stHeader"] button {
    color: #a0b8ff !important;
    background: rgba(77,142,255,0.1) !important;
    border: 1px solid rgba(77,142,255,0.3) !important;
    border-radius: 8px !important;
    visibility: visible !important;
    opacity: 1 !important;
}
[data-testid="stHeader"] button:hover {
    background: rgba(77,142,255,0.22) !important;
    border-color: #4d8eff !important;
}

/* SVG icons inside those buttons */
[data-testid="stHeader"] button svg,
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg {
    fill: #a0b8ff !important;
    color: #a0b8ff !important;
}

/* Raw icon ligature text e.g. "keyboard_double_arrow_right" — colour it on expand button */
[data-testid="stHeader"] button span,
[data-testid="collapsedControl"] span,
[data-testid="stSidebarCollapsedControl"] span {
    color: #a0b8ff !important;
    font-size: 13px !important;
}

/* Reset wrapper container if it's a div */
div[data-testid="stSidebarCollapseButton"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* ── Sidebar COLLAPSE button (button inside open sidebar that closes it) ── */
button[data-testid="stSidebarCollapseButton"],
div[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebar"] button[data-testid="baseButton-header"],
[data-testid="stSidebar"] button[kind="header"] {
    background: rgba(77,142,255,0.1) !important;
    border: 1px solid rgba(77,142,255,0.3) !important;
    border-radius: 8px !important;
    visibility: visible !important;
    opacity: 1 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 40px !important;
    height: 40px !important;
    box-sizing: border-box !important;
}

button[data-testid="stSidebarCollapseButton"]:hover,
div[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="stSidebar"] button[data-testid="baseButton-header"]:hover,
[data-testid="stSidebar"] button[kind="header"]:hover {
    background: rgba(77,142,255,0.22) !important;
    border-color: #4d8eff !important;
    box-shadow: 0 0 14px rgba(77,142,255,0.3) !important;
}

/* Inject left-arrow icon via SVG data URI — no font dependency */
button[data-testid="stSidebarCollapseButton"]::before,
div[data-testid="stSidebarCollapseButton"] button::before,
[data-testid="stSidebar"] button[data-testid="baseButton-header"]::before,
[data-testid="stSidebar"] button[kind="header"]::before {
    content: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='%23a0b8ff'%3E%3Cpath d='M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z'/%3E%3C/svg%3E");
    display: inline-block;
    line-height: 0;
    vertical-align: middle;
    pointer-events: none;
}

/* Hide existing SVG and raw text to avoid rendering issues */
button[data-testid="stSidebarCollapseButton"] svg,
div[data-testid="stSidebarCollapseButton"] button svg,
[data-testid="stSidebar"] button[data-testid="baseButton-header"] svg,
[data-testid="stSidebar"] button[kind="header"] svg {
    display: none !important;
}

button[data-testid="stSidebarCollapseButton"] span,
div[data-testid="stSidebarCollapseButton"] button span,
[data-testid="stSidebar"] button[data-testid="baseButton-header"] span,
[data-testid="stSidebar"] button[kind="header"] span {
    display: none !important;
}

[data-testid="stAppViewContainer"] > .main {
    background:
        radial-gradient(ellipse 80% 50% at 50% 0%, rgba(77,142,255,0.06) 0%, transparent 70%),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(0,230,118,0.03) 0%, transparent 60%),
        #060614;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #08081a !important;
    border-right: 1px solid rgba(100,120,255,0.1) !important;
}
/* Font only on wildcard — NOT color, to avoid leaking into native file input */
[data-testid="stSidebar"] * { font-family: 'DM Sans', sans-serif; }
/* Explicit color only on safe text elements */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] div[class],
[data-testid="stSidebar"] .stMarkdown { color: #c8c8e0; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #eeeeff; }
/* Force native file input text to be invisible so it can't double with styled button */
[data-testid="stFileUploaderDropzone"] input[type="file"] {
    color: transparent !important;
    font-size: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
    position: absolute !important;
    z-index: -1 !important;
}
/* Also zero-out any leftover span that duplicates button text */
[data-testid="stFileUploaderDropzone"] button span:first-child:not(:only-child) {
    display: none !important;
}

/* ── File uploader drop zone ── */
[data-testid="stFileUploaderDropzone"] {
    background: rgba(13,13,36,0.9) !important;
    border: 1.5px dashed rgba(77,142,255,0.4) !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 8px !important;
    transition: border-color 0.2s ease, background 0.2s ease !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: rgba(77,142,255,0.7) !important;
    background: rgba(77,142,255,0.05) !important;
}

/* Hide the cloud SVG icon and the redundant "Drag and drop" / "upload" paragraph
   inside the instructions — they cause the double-text overlap in the sidebar */
[data-testid="stFileUploaderDropzoneInstructions"] svg {
    display: none !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div > div {
    display: none !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div > p,
[data-testid="stFileUploaderDropzoneInstructions"] p {
    display: none !important;
}

/* Browse / Upload button */
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploaderDropzone"] [data-testid="baseButton-secondary"] {
    background: rgba(77,142,255,0.15) !important;
    border: 1px solid rgba(77,142,255,0.4) !important;
    border-radius: 8px !important;
    color: #a0b8ff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 7px 18px !important;
    width: auto !important;
    min-width: unset !important;
    max-width: 100% !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    transition: all 0.2s ease !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    background: rgba(77,142,255,0.25) !important;
    border-color: #4d8eff !important;
    color: #ffffff !important;
    box-shadow: 0 0 12px rgba(77,142,255,0.25) !important;
}

/* Keep size-limit text visible */
[data-testid="stFileUploaderDropzoneInstructions"] {
    color: #444466 !important;
    font-size: 11px !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small {
    color: #444466 !important;
    font-size: 11px !important;
    display: block !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span {
    color: #444466 !important;
    font-size: 11px !important;
}

/* Uploaded file chip */
[data-testid="stFileUploaderFile"] {
    background: rgba(77,142,255,0.08) !important;
    border: 1px solid rgba(77,142,255,0.2) !important;
    border-radius: 8px !important;
    padding: 4px 10px !important;
}
[data-testid="stFileUploaderFileName"] {
    color: #a0b8ff !important;
    font-size: 12px !important;
}
/* Delete file button — must not inherit the big .stButton width */
[data-testid="stFileUploaderDeleteBtn"] button {
    background: transparent !important;
    border: none !important;
    color: #555580 !important;
    width: auto !important;
    min-width: unset !important;
    padding: 2px 4px !important;
    box-shadow: none !important;
}
[data-testid="stFileUploaderDeleteBtn"] button:hover {
    color: #ff5252 !important;
    box-shadow: none !important;
    transform: none !important;
}

/* ── Metric cards ── */
.card-row { display: flex; gap: 16px; margin-bottom: 24px; }

.metric-card {
    flex: 1;
    background: #0d0d24;
    border: 1px solid rgba(100,120,255,0.08);
    border-radius: 16px;
    padding: 22px 24px 18px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease, transform 0.2s ease;
}
.metric-card:hover {
    border-color: rgba(100,120,255,0.2);
    transform: translateY(-2px);
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
}
.metric-card.green::before  { background: linear-gradient(90deg, #00e676, #00c853); }
.metric-card.amber::before  { background: linear-gradient(90deg, #ffb347, #ff8c00); }
.metric-card.red::before    { background: linear-gradient(90deg, #ff5252, #d32f2f); }
.metric-card.blue::before   { background: linear-gradient(90deg, #4d8eff, #1a5cff); }

.metric-value.blue { color: #4d8eff; }

.metric-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    color: #7a7a9a;
    font-weight: 400;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 38px;
    font-weight: 700;
    color: #4d8eff;
    line-height: 1;
    margin-bottom: 6px;
}
.metric-value.green { color: #00e676; }
.metric-value.red   { color: #ff5252; }
.metric-value.amber { color: #ffb347; }

.metric-sub {
    font-size: 11px;
    color: #444466;
    font-weight: 400;
}

/* ── Section titles ── */
.section-title {
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    font-weight: 500;
    color: #555580;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 28px 0 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(100,120,255,0.08);
}

/* ── Interpretation card ── */
.interp-card {
    background: #0d0d24;
    border: 1px solid rgba(77,142,255,0.12);
    border-radius: 16px;
    padding: 28px 32px;
    margin-top: 20px;
    margin-bottom: 32px;
    font-size: 15px;
    line-height: 1.7;
    color: #b0b0cc;
}
.interp-card strong { color: #eeeeff; font-weight: 600; }
.interp-card .flag  { color: #ffb347; font-weight: 600; }
.interp-card .good  { color: #00e676; font-weight: 600; }
.interp-card .bad   { color: #ff5252; font-weight: 600; }

/* ── Plotly chart containers ── */
.js-plotly-plot { border-radius: 16px; overflow: hidden; }

/* ── Streamlit button overrides ── */
.stButton > button {
    background: linear-gradient(135deg, #1a2a5e 0%, #0d1a3e 100%) !important;
    border: 1px solid rgba(77,142,255,0.35) !important;
    color: #a0b8ff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
}
.stButton > button:hover {
    border-color: #4d8eff !important;
    color: #fff !important;
    box-shadow: 0 0 18px rgba(77,142,255,0.25) !important;
    transform: translateY(-1px);
}
/* Primary run button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1a4aae 0%, #0d2a7e 100%) !important;
    border-color: rgba(77,142,255,0.6) !important;
    color: #d0e4ff !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #2a5aee 0%, #1a3abe 100%) !important;
    color: #fff !important;
    box-shadow: 0 0 24px rgba(77,142,255,0.4) !important;
}

/* ── Number input ── */
div[data-baseweb="input"] > div {
    background: #0d0d24 !important;
    border-color: rgba(100,120,255,0.2) !important;
    border-radius: 8px !important;
}
div[data-baseweb="input"] > div:focus-within {
    border-color: rgba(77,142,255,0.5) !important;
    box-shadow: 0 0 0 2px rgba(77,142,255,0.1) !important;
}

/* ── Slider ── */
[data-testid="stSlider"] > div > div > div > div {
    background: #4d8eff !important;
}

/* ── Widget labels ── */
label[data-testid="stWidgetLabel"] {
    color: #7a7a9a !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em !important;
    text-transform: uppercase !important;
}

/* ── Divider ── */
[data-testid="stSidebar"] hr {
    border-color: rgba(100,120,255,0.1) !important;
    margin: 12px 0 !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #060614; }
::-webkit-scrollbar-thumb { background: rgba(100,120,255,0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(100,120,255,0.4); }
</style>
""",
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style='display:flex;align-items:center;gap:10px;padding:4px 0 2px;'>
            <div style='width:32px;height:32px;background:linear-gradient(135deg,#1a2a5e,#0d4aae);
                        border-radius:8px;display:flex;align-items:center;justify-content:center;
                        font-size:16px;flex-shrink:0;border:1px solid rgba(77,142,255,0.3);'>🌌</div>
            <div>
                <div style='font-size:15px;font-weight:600;color:#eeeeff;line-height:1.2;'>Monte Carlo</div>
                <div style='font-size:11px;color:#444466;line-height:1.2;'>Probability space explorer</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    uploaded = st.file_uploader(
        "Upload backtest CSV",
        type=["csv"],
        help="CSV must contain columns: date, trade_return",
        label_visibility="visible",
    )

    st.markdown(
        "<div style='text-align:center;color:#444466;font-size:12px;margin:6px 0;'>— or —</div>",
        unsafe_allow_html=True,
    )
    use_demo = st.button("✦ Generate demo data")

    st.markdown("---")

    starting_capital = st.number_input(
        "Starting capital ($)",
        min_value=1_000,
        max_value=10_000_000,
        value=100_000,
        step=10_000,
    )

    n_simulations = st.slider(
        "Simulations",
        min_value=200,
        max_value=2_000,
        value=1_000,
        step=100,
    )

    st.markdown("---")
    run_btn = st.button("▶  Run simulation", type="primary")

# ── Session state ─────────────────────────────────────────────────────────────
if "trade_returns" not in st.session_state:
    st.session_state.trade_returns = None
if "results" not in st.session_state:
    st.session_state.results = None
if "data_label" not in st.session_state:
    st.session_state.data_label = ""

# ── Data loading ──────────────────────────────────────────────────────────────
if use_demo:
    df = generate_demo_data(200)
    st.session_state.trade_returns = df["trade_return"].values
    st.session_state.data_label = "Demo data · 200 trades"
    st.session_state.results = None

if uploaded is not None:
    try:
        raw = pd.read_csv(uploaded)
        ok, msg, cleaned = validate_csv(raw)
        if ok:
            st.session_state.trade_returns = cleaned["trade_return"].values
            st.session_state.data_label = f"{uploaded.name} · {len(cleaned)} trades"
            st.session_state.results = None
        else:
            st.error(msg)
    except Exception as e:
        st.error(f"Could not read file: {e}")

# ── Run simulation ────────────────────────────────────────────────────────────
if run_btn:
    if st.session_state.trade_returns is None:
        st.warning("Load data first — upload a CSV or generate demo data.")
    else:
        with st.spinner("Simulating probability space…"):
            st.session_state.results = run_monte_carlo(
                st.session_state.trade_returns,
                starting_capital=starting_capital,
                n_simulations=n_simulations,
            )

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<h1 style='font-family:"DM Sans",sans-serif;font-size:28px;font-weight:600;
           color:#eeeeff;margin-bottom:2px;'>Monte Carlo Simulation</h1>
<p style='font-size:13px;color:#555580;margin-top:0;'>
    Peer into the probability cloud of your strategy's possible futures.
</p>
""",
    unsafe_allow_html=True,
)

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.results is None:
    st.markdown(
        """
<div style='margin-top:80px;text-align:center;color:#2a2a4a;'>
    <div style='font-size:64px;'>🌌</div>
    <p style='font-family:"DM Sans",sans-serif;font-size:15px;color:#3a3a5a;margin-top:12px;'>
        Load data and run a simulation to see the probability nebula
    </p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.stop()

res = st.session_state.results
s = res["stats"]
equity_curves = res["equity_curves"]
final_values = res["final_values"]
max_drawdowns = res["max_drawdowns"]
original_equity = res["original_equity"]
n_steps = equity_curves.shape[1]
x_axis = np.arange(n_steps)

# ── Derived display stats ──────────────────────────────────────────────────────
trade_returns = st.session_state.trade_returns
win_rate = float(np.mean(trade_returns > 0))
avg_trade = float(np.mean(trade_returns))
total_compounded = float(np.prod(1.0 + trade_returns) - 1.0)
n_trades_disp = s["n_trades"]
source_label = "Generated" if "Demo" in (st.session_state.data_label or "") else "Uploaded"
n_loss_sims = int(round(s["prob_loss"] * s["n_simulations"]))
pct_rank_int = int(round(s["original_pct_rank"] * 100))

# ── Source / stats summary bar ─────────────────────────────────────────────────
avg_sign = "+" if avg_trade >= 0 else ""
total_sign = "+" if total_compounded >= 0 else ""
st.markdown(
    f"""
<div style='display:flex;align-items:center;gap:28px;padding:10px 18px;
            background:#0a0a1e;border:1px solid rgba(100,120,255,0.1);
            border-radius:10px;margin-bottom:20px;font-family:"Space Mono",monospace;
            font-size:12px;color:#7a7a9a;flex-wrap:wrap;'>
    <span>Source <span style='color:#eeeeff;font-weight:600;margin-left:6px;'>{source_label}</span></span>
    <span>Trades <span style='color:#eeeeff;font-weight:600;margin-left:6px;'>{n_trades_disp}</span></span>
    <span>Win Rate <span style='color:#00e676;font-weight:600;margin-left:6px;'>{win_rate*100:.1f}%</span></span>
    <span>Avg Trade <span style='color:#00e676;font-weight:600;margin-left:6px;'>{avg_sign}{avg_trade*100:.2f}%</span></span>
    <span>Total Compounded <span style='color:#00e676;font-weight:600;margin-left:6px;'>{total_sign}{total_compounded*100:.1f}%</span></span>
</div>
""",
    unsafe_allow_html=True,
)

# ── Top KPI cards ─────────────────────────────────────────────────────────────
prob_loss_color = "green" if s["prob_loss"] < 0.10 else ("amber" if s["prob_loss"] < 0.25 else "red")
median_ret = (s["median_final"] - s["starting_capital"]) / s["starting_capital"]
median_color = "green" if median_ret > 0 else "red"
dd95_color = "green" if s["p95_max_dd"] < 0.20 else ("amber" if s["p95_max_dd"] < 0.35 else "red")
overfit_color = "red" if s["overfitting_flag"] else "blue"

st.markdown(
    f"""
<div class="card-row">
    <div class="metric-card {prob_loss_color}">
        <div class="metric-label">Probability of Loss</div>
        <div class="metric-value {prob_loss_color}">{format_pct(s['prob_loss'])}</div>
        <div class="metric-sub">{n_loss_sims} / {s['n_simulations']:,} sims below {format_currency(s['starting_capital'])}</div>
    </div>
    <div class="metric-card {median_color}">
        <div class="metric-label">Median Return</div>
        <div class="metric-value {median_color}">{'+' if median_ret >= 0 else ''}{format_pct(median_ret)}</div>
        <div class="metric-sub">to {format_currency(s['median_final'])}</div>
    </div>
    <div class="metric-card {dd95_color}">
        <div class="metric-label">Worst 5% Drawdown</div>
        <div class="metric-value {dd95_color}">-{format_pct(s['p95_max_dd'])}</div>
        <div class="metric-sub">P(DD &gt; 20%): {format_pct(s['prob_dd_20'])} &nbsp; P(DD &gt; 30%): {format_pct(s['prob_dd_30'])}</div>
    </div>
    <div class="metric-card {overfit_color}">
        <div class="metric-label">Overfitting Risk</div>
        <div class="metric-value {overfit_color}">P{pct_rank_int}</div>
        <div class="metric-sub">Original within simulated range</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Fan Chart ─────────────────────────────────────────────────────────────────
st.markdown(f"<div class='section-title'>Probability Cloud &middot; {s['n_simulations']:,} Paths</div>", unsafe_allow_html=True)

# Sort curves by final value for colour gradient
sorted_idx = np.argsort(final_values)
n_sim = len(sorted_idx)

fig = go.Figure()

# Plot all simulation curves with colour gradient
# Group into thirds: bottom (red), middle (blue), top (green)
for rank, idx in enumerate(sorted_idx):
    frac = rank / n_sim  # 0 = worst, 1 = best
    if frac < 0.33:
        r, g, b = 255, 82, 82   # #ff5252
    elif frac < 0.67:
        r, g, b = 77, 142, 255  # #4d8eff
    else:
        r, g, b = 0, 230, 118   # #00e676

    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=equity_curves[idx],
            mode="lines",
            line=dict(color=f"rgba({r},{g},{b},0.013)", width=1),
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Percentile bands
p5  = np.percentile(equity_curves, 5,  axis=0)
p25 = np.percentile(equity_curves, 25, axis=0)
p75 = np.percentile(equity_curves, 75, axis=0)
p95 = np.percentile(equity_curves, 95, axis=0)
med = np.percentile(equity_curves, 50, axis=0)

# 5-95 band
fig.add_trace(go.Scatter(
    x=np.concatenate([x_axis, x_axis[::-1]]),
    y=np.concatenate([p95, p5[::-1]]),
    fill="toself",
    fillcolor="rgba(77,142,255,0.06)",
    line=dict(color="rgba(0,0,0,0)"),
    name="5–95th percentile",
    hoverinfo="skip",
))

# 25-75 band
fig.add_trace(go.Scatter(
    x=np.concatenate([x_axis, x_axis[::-1]]),
    y=np.concatenate([p75, p25[::-1]]),
    fill="toself",
    fillcolor="rgba(77,142,255,0.10)",
    line=dict(color="rgba(0,0,0,0)"),
    name="25–75th percentile",
    hoverinfo="skip",
))

# Median — glow layer
fig.add_trace(go.Scatter(
    x=x_axis, y=med,
    mode="lines",
    line=dict(color="rgba(77,142,255,0.25)", width=8),
    showlegend=False,
    hoverinfo="skip",
))
# Median — solid
fig.add_trace(go.Scatter(
    x=x_axis, y=med,
    mode="lines",
    line=dict(color="#4d8eff", width=2.5),
    name="Median",
))

# Original — glow
fig.add_trace(go.Scatter(
    x=x_axis, y=original_equity,
    mode="lines",
    line=dict(color="rgba(255,255,255,0.15)", width=10),
    showlegend=False,
    hoverinfo="skip",
))
# Original — solid white
fig.add_trace(go.Scatter(
    x=x_axis, y=original_equity,
    mode="lines",
    line=dict(color="#ffffff", width=2),
    name="Original backtest",
))

fig.update_layout(
    height=520,
    paper_bgcolor="#060614",
    plot_bgcolor="#060614",
    margin=dict(l=60, r=20, t=20, b=50),
    xaxis=dict(
        title="trade #",
        title_font=dict(color="#555580", size=11, family="DM Sans"),
        tickfont=dict(color="#555580", size=10, family="Space Mono"),
        gridcolor="rgba(100,120,255,0.04)",
        linecolor="rgba(100,120,255,0.08)",
        showgrid=True,
        zeroline=False,
    ),
    yaxis=dict(
        title="portfolio value ($)",
        title_font=dict(color="#555580", size=11, family="DM Sans"),
        tickfont=dict(color="#555580", size=10, family="Space Mono"),
        gridcolor="rgba(100,120,255,0.04)",
        linecolor="rgba(100,120,255,0.08)",
        showgrid=True,
        zeroline=False,
        tickprefix="$",
        tickformat=",.0f",
    ),
    legend=dict(
        font=dict(color="#7a7a9a", size=11, family="DM Sans"),
        bgcolor="rgba(13,13,36,0.8)",
        bordercolor="rgba(100,120,255,0.12)",
        borderwidth=1,
        x=0.02, y=0.98,
    ),
    hovermode="x unified",
)

st.plotly_chart(fig, width="stretch")

# ── Lower charts ──────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Outcome Distributions</div>", unsafe_allow_html=True)
col_left, col_right = st.columns(2)

# Final portfolio value histogram
with col_left:
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(
        x=final_values,
        nbinsx=60,
        marker=dict(
            color="rgba(77,142,255,0.12)",
            line=dict(color="#4d8eff", width=0.8),
        ),
        name="Simulations",
    ))
    fig2.add_vline(
        x=s["original_final"],
        line=dict(color="white", width=1.5, dash="dash"),
        annotation_text="Original",
        annotation_position="top",
        annotation_font=dict(color="white", size=10, family="DM Sans"),
    )
    fig2.add_vline(
        x=s["starting_capital"],
        line=dict(color="#ff5252", width=1, dash="dot"),
        annotation_text="break-even",
        annotation_font=dict(color="#ff5252", size=10, family="DM Sans"),
    )
    fig2.update_layout(
        height=300,
        paper_bgcolor="#060614",
        plot_bgcolor="#060614",
        margin=dict(l=50, r=16, t=30, b=60),
        showlegend=False,
        xaxis=dict(
            title="Final Portfolio Value ($)",
            title_font=dict(color="#555580", size=10, family="DM Sans"),
            tickfont=dict(color="#555580", size=9, family="Space Mono"),
            gridcolor="rgba(100,120,255,0.04)",
            tickprefix="$", tickformat=",.0f",
        ),
        yaxis=dict(
            title="Simulations",
            title_font=dict(color="#555580", size=10, family="DM Sans"),
            tickfont=dict(color="#555580", size=9, family="Space Mono"),
            gridcolor="rgba(100,120,255,0.04)",
        ),
    )
    st.plotly_chart(fig2, width="stretch")

# Max drawdown histogram  (displayed as negative %)
with col_right:
    fig3 = go.Figure()
    fig3.add_trace(go.Histogram(
        x=max_drawdowns * -100,   # negative so axis reads -30, -20 etc.
        nbinsx=60,
        marker=dict(
            color="rgba(255,82,82,0.12)",
            line=dict(color="#ff5252", width=0.8),
        ),
        name="Simulations",
    ))
    fig3.add_vline(
        x=s["original_dd"] * -100,
        line=dict(color="white", width=1.5, dash="dash"),
        annotation_text="Original",
        annotation_position="top",
        annotation_font=dict(color="white", size=10, family="DM Sans"),
    )
    fig3.update_layout(
        height=300,
        paper_bgcolor="#060614",
        plot_bgcolor="#060614",
        margin=dict(l=50, r=16, t=30, b=60),
        showlegend=False,
        xaxis=dict(
            title="Max Drawdown (%)",
            title_font=dict(color="#555580", size=10, family="DM Sans"),
            tickfont=dict(color="#555580", size=9, family="Space Mono"),
            gridcolor="rgba(100,120,255,0.04)",
            ticksuffix="%",
        ),
        yaxis=dict(
            title="Simulations",
            title_font=dict(color="#555580", size=10, family="DM Sans"),
            tickfont=dict(color="#555580", size=9, family="Space Mono"),
            gridcolor="rgba(100,120,255,0.04)",
        ),
    )
    st.plotly_chart(fig3, width="stretch")

# ── Interpretation card ───────────────────────────────────────────────────────
_rank_ord = (
    "st" if pct_rank_int % 100 in (11, 12, 13) else
    ("st" if pct_rank_int % 10 == 1 else
     ("nd" if pct_rank_int % 10 == 2 else
      ("rd" if pct_rank_int % 10 == 3 else "th")))
)
rank_label = f"{pct_rank_int}{_rank_ord}"

if s["overfitting_flag"]:
    overfit_sentence = (
        f"The original backtest ranked at the "
        f"<span style='color:#ffb347;font-weight:600;'>{rank_label}</span> percentile of simulated outcomes — "
        f"<span class='flag'>suspiciously high — potential overfitting detected.</span>"
    )
else:
    overfit_sentence = (
        f"The original backtest ranked at the "
        f"<span style='color:#4d8eff;font-weight:600;'>{rank_label}</span> percentile of simulated outcomes — "
        f"<span class='good'>firmly inside the bell of outcomes — not overfit.</span>"
    )

median_sign = "+" if median_ret >= 0 else ""

st.markdown(
    f"""
<div class="interp-card">
    <p style="margin:0 0 6px 0;
              font-family:'DM Sans',sans-serif;font-size:11px;font-weight:600;
              letter-spacing:0.1em;text-transform:uppercase;color:#4d8eff;">
        Interpretation
    </p>
    <p style="margin-top:0;">
        Across <strong>{s['n_simulations']:,}</strong> simulations shuffling
        <strong>{s['n_trades']}</strong> trades with ±0.3% per-trade noise, a
        {format_currency(s['starting_capital'])} starting stake produced a median outcome of
        <strong>{format_currency(s['median_final'])}</strong> ({median_sign}{format_pct(median_ret)}).
        The 5th–95th percentile outcome range was
        <strong>{format_currency(s['p5_final'])}</strong> to
        <strong>{format_currency(s['p95_final'])}</strong>.
    </p>
    <p>
        Probability of ending below starting capital:
        <strong>{format_pct(s['prob_loss'])}</strong>.
        Probability of a 20% drawdown: <strong>{format_pct(s['prob_dd_20'])}</strong>;
        of a 30% drawdown: <strong>{format_pct(s['prob_dd_30'])}</strong>.
    </p>
    <p style="margin-bottom:0;">{overfit_sentence}</p>
</div>
""",
    unsafe_allow_html=True,
)