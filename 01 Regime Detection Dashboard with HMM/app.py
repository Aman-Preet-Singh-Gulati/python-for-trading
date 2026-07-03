"""
Regime Detection Dashboard
---------------------------
Detects volatility regimes in daily price data using a Gaussian HMM,
selecting the number of regimes via BIC, and inferring the regime at each
bar with a strictly causal forward filter (never Viterbi, never
forward-backward smoothing) so there is no look-ahead bias.

Run with: streamlit run app.py
"""

import warnings
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from design_system import *
from regime_engine import REGIME_NAME_SCHEMES, run_pipeline

warnings.filterwarnings("ignore")

apply_theme(page_title="Regime Detection Dashboard", page_icon="◈")


def _hex_to_rgba_local(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i: i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# ==========================================================================
# DATA (the only network-dependent piece — cached, kept separate from the
# pure-python regime_engine pipeline so that pipeline can be unit tested
# without hitting the network)
# ==========================================================================

@st.cache_data(show_spinner=False, ttl=3600)
def download_data(ticker: str, start: date, end: date) -> pd.DataFrame:
    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    return df[keep].dropna()


# ==========================================================================
# CHART BUILDERS
# ==========================================================================

def build_price_chart(out: pd.DataFrame) -> go.Figure:
    fig = go.Figure(layout=get_plotly_layout(height=560, show_legend=False))

    # contiguous regime segments -> background bands at 12-15% opacity
    labels = out["final_label"].values
    idx = out.index
    seg_start = 0
    for t in range(1, len(labels) + 1):
        if t == len(labels) or labels[t] != labels[seg_start]:
            color = regime_color(labels[seg_start])
            fig.add_vrect(
                x0=idx[seg_start],
                x1=idx[t - 1] if t - 1 < len(idx) else idx[-1],
                fillcolor=color,
                opacity=0.14,
                layer="below",
                line_width=0,
            )
            seg_start = t

    fig.add_trace(
        go.Scatter(
            x=idx,
            y=out["close"],
            mode="lines",
            line=dict(color=TEXT_PRIMARY, width=1.8),
            name="Close",
            hovertemplate="%{x|%Y-%m-%d}<br>Close: %{y:.2f}<extra></extra>",
        )
    )
    fig.update_layout(yaxis_title="Price", margin=dict(l=50, r=30, t=10, b=40))
    return fig


def build_confidence_chart(out: pd.DataFrame) -> go.Figure:
    fig = go.Figure(layout=get_plotly_layout(height=220, show_legend=False))
    fig.add_trace(
        go.Scatter(
            x=out.index,
            y=out["confidence"] * 100,
            mode="lines",
            line=dict(color=ACCENT_CYAN, width=1.6),
            fill="tozeroy",
            fillcolor=_hex_to_rgba_local(ACCENT_CYAN, 0.30),
            name="Confidence",
            hovertemplate="%{x|%Y-%m-%d}<br>Confidence: %{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        yaxis_title="Confidence %",
        yaxis=dict(range=[0, 100]),
        margin=dict(l=50, r=30, t=10, b=30),
    )
    return fig


# ==========================================================================
# SIDEBAR
# ==========================================================================

with st.sidebar:
    st.markdown(
        f"<div style='font-family:{FONT_DISPLAY};color:{ACCENT_CYAN};font-size:0.95rem;"
        f"letter-spacing:0.05em;margin-bottom:2px;'>◈ REGIME DETECTOR</div>",
        unsafe_allow_html=True,
    )
    st.caption("Causal HMM volatility regime inference")
    st.markdown("---")

    ticker_input = st.text_input("Ticker", value="SPY").upper().strip()

    default_end = date.today()
    default_start = default_end - timedelta(days=3 * 365)
    date_range = st.date_input(
        "Date Range",
        value=(default_start, default_end),
        max_value=default_end,
    )

    k_override = st.selectbox(
        "Number of Regimes",
        options=["Auto (BIC)", 3, 4, 5, 6, 7],
        index=0,
        help="Auto (BIC) tests 3–7 regimes and picks the best by Bayesian Information Criterion.",
    )

    st.markdown("---")
    run_clicked = st.button("▶  Run Analysis", width="stretch", type="primary")

    with st.expander("About the method", expanded=False):
        st.caption(
            "Regimes are inferred with a Gaussian HMM fit on standardized "
            "return, volatility, volume, and range features. The regime at "
            "each bar comes from a forward-only causal filter — never the "
            "Viterbi path and never forward-backward smoothing — so the "
            "label at time T uses only information available through T."
        )

# ==========================================================================
# RUN / CACHE RESULTS
# ==========================================================================

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = default_start, default_end

if "results" not in st.session_state:
    run_clicked = True  # auto-run once on first load with defaults

if run_clicked:
    with st.spinner(f"Downloading {ticker_input} and fitting regime model..."):
        raw_prices = download_data(ticker_input, start_date, end_date)
        st.session_state["results"] = run_pipeline(raw_prices, k_override)
        st.session_state["ticker"] = ticker_input

results = st.session_state.get("results")

# ==========================================================================
# MAIN LAYOUT
# ==========================================================================

if results is None:
    st.info("Configure parameters in the sidebar and click **Run Analysis**.")
    st.stop()

if results.get("error"):
    st.error(results["error"])
    st.stop()

out = results["df"]
ticker_disp = st.session_state.get("ticker", ticker_input)
current_row = out.iloc[-1]
current_label = current_row["final_label"]
current_conf = current_row["confidence"]
last20 = out["flagged_uncertain"].iloc[-20:]
is_stable = not bool(current_row["flagged_uncertain"])

# ---- Top status bar -------------------------------------------------
c1, c2, c3, c4, c5 = st.columns([1.6, 1.6, 1.1, 1.3, 1.1])
with c1:
    st.markdown(
        f"<div style='color:{TEXT_SECONDARY};font-size:0.72rem;letter-spacing:0.1em;"
        f"text-transform:uppercase;font-weight:600;'>Ticker</div>"
        f"<div style='font-family:{FONT_DISPLAY};font-size:2.1rem;font-weight:700;"
        f"color:{TEXT_PRIMARY};line-height:1.2;'>{ticker_disp}</div>",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"<div style='color:{TEXT_SECONDARY};font-size:0.72rem;letter-spacing:0.1em;"
        f"text-transform:uppercase;font-weight:600;margin-bottom:6px;'>Current Regime</div>",
        unsafe_allow_html=True,
    )
    regime_badge(current_label, glow=True)
with c3:
    kpi_value("Confidence", f"{current_conf*100:.1f}%", color=ACCENT_CYAN)
with c4:
    status_text = "Stable" if is_stable else "Uncertain"
    status_color = ACCENT_GREEN if is_stable else ACCENT_AMBER
    kpi_value("Stability", status_text, color=status_color,
              sublabel=f"{int(last20.sum())} flips / last 20 bars")
with c5:
    kpi_value("Regimes Detected", str(results["best_k"]), color=ACCENT_MAGENTA,
              sublabel="Auto (BIC)" if k_override == "Auto (BIC)" else "Manual override")

bias_color = ACCENT_GREEN if results["lookahead_passed"] else ACCENT_RED
bias_text = "No look-ahead bias detected" if results["lookahead_passed"] else "LOOK-AHEAD BIAS DETECTED"
st.markdown(
    f"<div style='margin-top:14px;color:{bias_color};font-size:0.78rem;font-family:{FONT_DISPLAY};'>"
    f"● {bias_text} — forward-filter only, truncation-overlap Δ = {results['lookahead_diff']:.2e}"
    f"</div>",
    unsafe_allow_html=True,
)

with st.expander("Model selection details (BIC across k = 3–7)"):
    bic_df = pd.DataFrame(results["bic_table"], columns=["k", "BIC", "Log-Likelihood"]).set_index("k")
    st.dataframe(bic_df.style.format({"BIC": "{:.1f}", "Log-Likelihood": "{:.1f}"}), width="stretch")
    st.caption(f"Selected k = {results['best_k']} (lowest BIC = {results['best_bic']:.1f}).")

st.markdown("<div style='margin:18px 0;'></div>", unsafe_allow_html=True)

# ---- Hero chart -------------------------------------------------------
section_header("Price & Regime Timeline", "Background shading = active regime")
st.plotly_chart(build_price_chart(out), width="stretch", config={"displayModeBar": False})

# ---- Regime statistics grid -------------------------------------------
section_header("Regime Statistics")

present_labels = list(out["final_label"].unique())
order_hint = REGIME_NAME_SCHEMES[results["best_k"]] + ["Uncertain"]
present_labels.sort(key=lambda l: order_hint.index(l) if l in order_hint else 999)

grouped = out.groupby("final_label")
total_bars = len(out)

n_cols = min(4, max(1, len(present_labels)))
cols = st.columns(n_cols)
for i, label in enumerate(present_labels):
    g = grouped.get_group(label)
    pct_time = len(g) / total_bars * 100
    metrics = {
        "Mean Return": f"{g['log_return'].mean()*100:+.3f}%",
        "Mean Volatility": f"{g['realized_vol'].mean()*100:.3f}%",
        "Mean Vol. Ratio": f"{g['volume_ratio'].mean():.2f}x",
        "Time in Regime": f"{pct_time:.1f}%",
    }
    with cols[i % n_cols]:
        metric_card(label, metrics, border_color=regime_color(label),
                    footer=f"{len(g)} bars")

# ---- Confidence timeline -----------------------------------------------
section_header("Confidence Timeline", "Filtered probability of the active regime, per bar")
st.plotly_chart(build_confidence_chart(out), width="stretch", config={"displayModeBar": False})

st.markdown(
    f"<div style='margin-top:24px;color:{TEXT_MUTED};font-size:0.72rem;text-align:center;'>"
    f"Regime detection is statistical, not predictive. Nothing here is investment advice."
    f"</div>",
    unsafe_allow_html=True,
)