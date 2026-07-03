"""
sensitivity_dashboard.py — Strategy Sensitivity Analysis Dashboard
SMA crossover robustness analysis across parameter space.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

from utils import (
    fetch_price_data,
    run_sma_crossover,
    sweep_parameter,
    compute_parameter_robustness,
    overall_robustness,
    robustness_label,
    build_heatmap_data,
    METRIC_COLS,
)

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Sensitivity Analysis",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>
/* ── Base ────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0f1117;
    color: #e2e8f0;
}
.stApp { background-color: #0f1117; }

/* ── Sidebar ──────────────────────────────────────────────────────────*/
[data-testid="stSidebar"] {
    background-color: #13151e !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 11px;
    letter-spacing: 0.12em;
    color: #6b7280;
    text-transform: uppercase;
    font-weight: 500;
    margin-bottom: 12px;
    margin-top: 24px;
}
[data-testid="stSidebar"] label {
    font-size: 13px;
    color: #9ca3af;
    font-family: 'IBM Plex Sans', sans-serif;
}

/* ── Main padding ───────────────────────────────────────────────────── */
.main .block-container {
    padding: 2.5rem 3rem 4rem 3rem;
    max-width: 1400px;
}

/* ── Typography ─────────────────────────────────────────────────────── */
.page-title {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 30px;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.02em;
    margin-bottom: 8px;
}
.page-subtitle {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 14px;
    color: #6b7280;
    font-weight: 400;
    margin-bottom: 10px;
    line-height: 1.6;
}
.config-bar {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 36px;
    letter-spacing: 0.01em;
}
.section-title {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 18px;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 6px;
    margin-top: 0;
}
.section-subtitle {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 13px;
    color: #6b7280;
    margin-bottom: 20px;
    line-height: 1.6;
}
.section-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin: 40px 0;
}

/* ── KPI metric cards ────────────────────────────────────────────────── */
.metric-card {
    background: #1a1c25;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 18px 20px 14px;
}
.metric-label-top {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 11px;
    color: #6b7280;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.metric-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 30px;
    font-weight: 600;
    color: #f1f5f9;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin-bottom: 5px;
}
.metric-sublabel {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 11px;
    color: #6b7280;
    font-weight: 400;
    margin-top: 2px;
}
.metric-positive { color: #22c55e; }
.metric-negative { color: #ef4444; }
.metric-neutral  { color: #f1f5f9; }

/* ── Gauge labels ────────────────────────────────────────────────────── */
.gauge-section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.14em;
    color: #6b7280;
    text-transform: uppercase;
    text-align: center;
    margin-top: -6px;
    margin-bottom: 4px;
}
.gauge-verdict {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-align: center;
    margin-bottom: 8px;
}

/* ── Buttons ─────────────────────────────────────────────────────────── */
.stButton > button {
    background: #22c55e;
    color: #0f1117;
    border: none;
    border-radius: 6px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 10px 24px;
    width: 100%;
    transition: background 0.15s ease;
}
.stButton > button:hover { background: #16a34a; color: #0f1117; }

/* ── Number inputs ───────────────────────────────────────────────────── */
.stNumberInput input {
    background: #1a1c25 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #e2e8f0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 13px !important;
    border-radius: 6px !important;
}

/* ── Spinner ──────────────────────────────────────────────────────────── */
.stSpinner { color: #22c55e !important; }

/* ── Hide Streamlit chrome ───────────────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: visible; }
[data-testid="stHeader"] { background: transparent; }

/* ── Alert boxes ─────────────────────────────────────────────────────── */
.stAlert {
    background: #1a1c25 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Constants & helpers
# ──────────────────────────────────────────────────────────────────────────────

DARK_BG   = "#0f1117"
CARD_BG   = "#1a1c25"
GREEN     = "#22c55e"
AMBER     = "#f59e0b"
RED       = "#ef4444"
TEAL      = "#06b6d4"
MUTED     = "#9ca3af"
MONO_FONT = "IBM Plex Mono"

# Base Plotly layout — xaxis/yaxis/margin intentionally omitted so each
# chart function can supply its own without a "multiple values" kwarg error.
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=CARD_BG,
    font_family=MONO_FONT,
    font_color="#e2e8f0",
)


def fmt_param_val(v) -> str:
    """Format a parameter value: integer if whole, one decimal place if float."""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    elif isinstance(v, float):
        return f"{v:.1f}"
    return str(v)


def deviation_color(dev: float) -> str:
    if dev <= 0.10:
        return "rgba(34,197,94,0.70)"
    elif dev <= 0.20:
        return "rgba(6,182,212,0.50)"
    elif dev <= 0.40:
        return "rgba(245,158,11,0.50)"
    else:
        return "rgba(239,68,68,0.50)"


# ──────────────────────────────────────────────────────────────────────────────
# Gauge — multicolor zone arc
# ──────────────────────────────────────────────────────────────────────────────

def make_gauge(score: float) -> go.Figure:
    label, color_key = robustness_label(score)
    arc_color = {"green": GREEN, "amber": AMBER, "red": RED}[color_key]

    fig = go.Figure()
    r_outer, r_inner = 1.0, 0.62

    def _arc(a_start, a_end, n=300):
        theta = np.linspace(a_start, a_end, n)
        xo = np.cos(np.radians(theta)) * r_outer
        yo = np.sin(np.radians(theta)) * r_outer
        xi = np.cos(np.radians(theta[::-1])) * r_inner
        yi = np.sin(np.radians(theta[::-1])) * r_inner
        return np.concatenate([xo, xi]), np.concatenate([yo, yi])

    # Background zone arcs: red 0–40, amber 40–70, green 70–100
    for a0, a1, fill in [
        (180.0,           180 - 0.40*180, "rgba(239,68,68,0.30)"),
        (180 - 0.40*180,  180 - 0.70*180, "rgba(245,158,11,0.30)"),
        (180 - 0.70*180,  0.0,            "rgba(34,197,94,0.30)"),
    ]:
        x, y = _arc(a0, a1)
        fig.add_trace(go.Scatter(x=x, y=y, fill="toself", fillcolor=fill,
                                 line=dict(color="rgba(0,0,0,0)"),
                                 hoverinfo="skip", showlegend=False))

    # Filled arc up to current score
    x_f, y_f = _arc(180, 180 - (score / 100) * 180)
    fig.add_trace(go.Scatter(x=x_f, y=y_f, fill="toself", fillcolor=arc_color,
                             line=dict(color="rgba(0,0,0,0)"),
                             hoverinfo="skip", showlegend=False))

    # Score number
    fig.add_annotation(x=0, y=0.18, text=f"<b>{score:.0f}</b>",
                       font=dict(family=MONO_FONT, size=54, color=arc_color),
                       showarrow=False)

    # Tick labels at zone boundaries
    for val, lbl in [(0, "0"), (40, "40"), (70, "70"), (100, "100")]:
        angle = 180 - (val / 100) * 180
        rad = np.radians(angle)
        fig.add_annotation(
            x=np.cos(rad) * 1.17, y=np.sin(rad) * 1.17, text=lbl,
            font=dict(family=MONO_FONT, size=9, color=MUTED),
            showarrow=False,
        )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=260,
        xaxis=dict(visible=False, range=[-1.25, 1.25]),
        yaxis=dict(visible=False, range=[-0.2, 1.25], scaleanchor="x", scaleratio=1),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# Heatmap
# ──────────────────────────────────────────────────────────────────────────────

METRIC_DISPLAY = {
    "total_return": "Total Return",
    "sharpe_ratio": "Sharpe",
    "max_drawdown": "Max Drawdown",
    "win_rate":     "Win Rate",
}

PARAM_DISPLAY = {
    "fast_ma":        "Fast MA",
    "slow_ma":        "Slow MA",
    "stop_loss_pct":  "Stop Loss %",
    "take_profit_pct": "Take Profit %",
}


def make_heatmap(heatmap_df: pd.DataFrame) -> go.Figure:
    params  = [PARAM_DISPLAY.get(p, p) for p in heatmap_df.index.tolist()]
    metrics = [METRIC_DISPLAY.get(m, m) for m in METRIC_COLS]
    z = heatmap_df[METRIC_COLS].values
    text = [[f"{v*100:.0f}%" if not np.isnan(v) else "–" for v in row] for row in z]

    fig = go.Figure(data=go.Heatmap(
        z=z, x=metrics, y=params,
        text=text,
        texttemplate="%{text}",
        textfont=dict(family=MONO_FONT, size=14, color="#f1f5f9"),
        colorscale=[
            [0.00, "rgba(34,197,94,0.70)"],
            [0.10, "rgba(34,197,94,0.70)"],
            [0.20, "rgba(6,182,212,0.50)"],
            [0.40, "rgba(245,158,11,0.50)"],
            [1.00, "rgba(239,68,68,0.50)"],
        ],
        zmin=0, zmax=1,
        showscale=False,
        xgap=4, ygap=4,
        hovertemplate="<b>%{y}</b><br>%{x}: %{text}<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=260,
        xaxis=dict(side="top",
                   tickfont=dict(size=13, family="IBM Plex Sans", color="#e2e8f0"),
                   gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(tickfont=dict(size=13, family="IBM Plex Sans", color="#e2e8f0"),
                   gridcolor="rgba(0,0,0,0)",
                   autorange="reversed"),
        margin=dict(l=10, r=10, t=44, b=10),
    )
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# Per-parameter sensitivity line chart
# ──────────────────────────────────────────────────────────────────────────────

def make_sensitivity_chart(
    sweep_df: pd.DataFrame,
    param_name: str,
    base_val: float,
    metric: str = "total_return",
) -> go.Figure:
    x = sweep_df["param_value"].values
    y = sweep_df[metric].values  # raw decimal

    base_y = sweep_df.loc[
        (sweep_df["param_value"] - base_val).abs().idxmin(), metric
    ]

    # ±10% stable band
    band_lo = base_y * 0.90 if abs(base_y) > 1e-9 else 0
    band_hi = base_y * 1.10 if abs(base_y) > 1e-9 else 0

    fig = go.Figure()

    # Stable zone band (y in %)
    fig.add_trace(go.Scatter(
        x=np.concatenate([x, x[::-1]]),
        y=np.concatenate([
            np.full_like(x, band_hi * 100),
            np.full_like(x, band_lo * 100)[::-1],
        ]),
        fill="toself",
        fillcolor="rgba(34,197,94,0.09)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip", showlegend=False,
    ))

    # Main line + markers
    fig.add_trace(go.Scatter(
        x=x, y=y * 100,
        mode="lines+markers",
        line=dict(color="#ffffff", width=1.8),
        marker=dict(size=5, color="#ffffff", symbol="circle"),
        hovertemplate=(
            f"<b>{PARAM_DISPLAY.get(param_name, param_name)}</b> = %{{x}}<br>"
            f"Total Return: %{{y:.1f}}%<extra></extra>"
        ),
        showlegend=False,
    ))

    # Base vline
    fig.add_vline(
        x=base_val,
        line=dict(color=GREEN, width=1.5, dash="dash"),
        annotation_text=f"base = {fmt_param_val(base_val)}",
        annotation_font=dict(family=MONO_FONT, size=10, color=GREEN),
        annotation_position="top right",
    )

    param_label = PARAM_DISPLAY.get(param_name, param_name)

    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=230,
        xaxis=dict(
            title=dict(text=param_label,
                       font=dict(size=11, color=MUTED, family="IBM Plex Sans")),
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(size=10, color=MUTED, family=MONO_FONT),
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text="Total Return (%)",
                       font=dict(size=11, color=MUTED, family="IBM Plex Sans")),
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(size=10, color=MUTED, family=MONO_FONT),
            zeroline=False,
            ticksuffix="%",
        ),
        margin=dict(l=55, r=24, t=30, b=48),
    )
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Instrument")
    ticker = st.text_input("Ticker", value="SPY", help="Yahoo Finance ticker symbol")

    st.markdown("### Date Range")
    default_end   = datetime.date.today()
    default_start = default_end - datetime.timedelta(days=5 * 365)
    start_date = st.date_input("From", value=default_start)
    end_date   = st.date_input("To",   value=default_end)

    st.markdown("### Base Parameters")
    fast_ma_base     = st.number_input("Fast MA (periods)",  min_value=2,   max_value=50,   value=10,  step=1)
    slow_ma_base     = st.number_input("Slow MA (periods)",  min_value=10,  max_value=200,  value=50,  step=5)
    stop_loss_base   = st.number_input("Stop Loss %",        min_value=0.5, max_value=20.0, value=2.0, step=0.5, format="%.1f")
    take_profit_base = st.number_input("Take Profit %",      min_value=0.5, max_value=30.0, value=4.0, step=0.5, format="%.1f")

    st.markdown("### Sweep Ranges")

    with st.expander("Fast MA sweep"):
        fast_min  = st.number_input("Min",  value=5,  key="f_min",  min_value=2, max_value=50)
        fast_max  = st.number_input("Max",  value=30, key="f_max",  min_value=3, max_value=100)
        fast_step = st.number_input("Step", value=1,  key="f_step", min_value=1, max_value=10)

    with st.expander("Slow MA sweep"):
        slow_min  = st.number_input("Min",  value=20,  key="s_min",  min_value=5,  max_value=200)
        slow_max  = st.number_input("Max",  value=100, key="s_max",  min_value=10, max_value=300)
        slow_step = st.number_input("Step", value=5,   key="s_step", min_value=1,  max_value=20)

    with st.expander("Stop Loss % sweep"):
        sl_min  = st.number_input("Min",  value=0.5, key="sl_min",  min_value=0.1, max_value=10.0, step=0.5, format="%.1f")
        sl_max  = st.number_input("Max",  value=5.0, key="sl_max",  min_value=0.5, max_value=30.0, step=0.5, format="%.1f")
        sl_step = st.number_input("Step", value=0.5, key="sl_step", min_value=0.1, max_value=5.0,  step=0.1, format="%.1f")

    with st.expander("Take Profit % sweep"):
        tp_min  = st.number_input("Min",  value=1.0,  key="tp_min",  min_value=0.5, max_value=20.0, step=0.5, format="%.1f")
        tp_max  = st.number_input("Max",  value=10.0, key="tp_max",  min_value=1.0, max_value=50.0, step=0.5, format="%.1f")
        tp_step = st.number_input("Step", value=0.5,  key="tp_step", min_value=0.1, max_value=5.0,  step=0.1, format="%.1f")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    run_btn = st.button("Run Analysis", key="run")


# ──────────────────────────────────────────────────────────────────────────────
# Page header
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class='page-title'>Strategy Sensitivity Analysis</div>
<div class='page-subtitle'>
    SMA crossover on a ticker of your choice — how much do results change
    when each parameter moves across its range?
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────────────────────────────────────

if "results" not in st.session_state:
    st.session_state.results = None


# ──────────────────────────────────────────────────────────────────────────────
# Run analysis
# ──────────────────────────────────────────────────────────────────────────────

if run_btn:
    base_params = {
        "fast_ma":        fast_ma_base,
        "slow_ma":        slow_ma_base,
        "stop_loss_pct":  stop_loss_base,
        "take_profit_pct": take_profit_base,
    }
    sweep_defs = {
        "fast_ma":         np.arange(fast_min, fast_max + fast_step, fast_step),
        "slow_ma":         np.arange(slow_min, slow_max + slow_step, slow_step),
        "stop_loss_pct":   np.arange(sl_min,   sl_max  + sl_step,  sl_step),
        "take_profit_pct": np.arange(tp_min,   tp_max  + tp_step,  tp_step),
    }

    with st.spinner("Fetching price data…"):
        try:
            prices = fetch_price_data(ticker, str(start_date), str(end_date))
        except Exception as e:
            st.error(f"Could not fetch data for **{ticker}**: {e}")
            st.stop()

    with st.spinner("Running base backtest…"):
        base_result = run_sma_crossover(prices, **base_params)
        base_metrics = {
            "total_return": base_result.total_return,
            "sharpe_ratio": base_result.sharpe_ratio,
            "max_drawdown": base_result.max_drawdown,
            "win_rate":     base_result.win_rate,
        }
        n_trades = len(base_result.equity_curve) - 1

    sweep_results = {}
    with st.spinner("Running parameter sweeps…"):
        progress_bar = st.progress(0)
        params_list  = list(sweep_defs.items())
        for i, (pname, pvals) in enumerate(params_list):
            sweep_results[pname] = sweep_parameter(
                prices, pname, list(pvals), base_params
            )
            progress_bar.progress((i + 1) / len(params_list))
        progress_bar.empty()

    per_param_scores = {
        p: compute_parameter_robustness(df) for p, df in sweep_results.items()
    }
    overall_score = overall_robustness(per_param_scores)
    heatmap_df    = build_heatmap_data(sweep_results, base_params, base_metrics)

    st.session_state.results = {
        "base_params":      base_params,
        "base_metrics":     base_metrics,
        "sweep_results":    sweep_results,
        "per_param_scores": per_param_scores,
        "overall_score":    overall_score,
        "heatmap_df":       heatmap_df,
        "ticker":           ticker,
        "start_date":       str(start_date),
        "end_date":         str(end_date),
        "n_trades":         n_trades,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Render results
# ──────────────────────────────────────────────────────────────────────────────

if st.session_state.results:
    R = st.session_state.results
    base_metrics     = R["base_metrics"]
    per_param_scores = R["per_param_scores"]
    overall_score    = R["overall_score"]
    sweep_results    = R["sweep_results"]
    heatmap_df       = R["heatmap_df"]
    base_params      = R["base_params"]
    n_trades         = R.get("n_trades", 0)

    # ── Config bar ───────────────────────────────────────────────────────────
    bp = base_params
    st.markdown(
        f"<div class='config-bar'>"
        f"{R['ticker']} · {R.get('start_date', '')} → {R.get('end_date', '')} · "
        f"base = Fast {int(bp['fast_ma'])}, Slow {int(bp['slow_ma'])}, "
        f"Stop {bp['stop_loss_pct']:.1f}%, Take {bp['take_profit_pct']:.1f}%"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Gauge + KPI cards ────────────────────────────────────────────────────
    col_gauge, col_metrics = st.columns([1, 2.5], gap="large")

    with col_gauge:
        gauge_label, gauge_ck = robustness_label(overall_score)
        gauge_color = {"green": GREEN, "amber": AMBER, "red": RED}[gauge_ck]
        st.plotly_chart(
            make_gauge(overall_score),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.markdown(
            f"<div class='gauge-section-label'>Strategy Robustness</div>"
            f"<div class='gauge-verdict' style='color:{gauge_color};'>"
            f"{gauge_label.upper()}</div>",
            unsafe_allow_html=True,
        )

    with col_metrics:
        st.markdown(
            "<div style='font-family:IBM Plex Sans;font-size:16px;font-weight:600;"
            "color:#f1f5f9;margin-bottom:16px;margin-top:6px;'>"
            "Base Strategy Performance</div>",
            unsafe_allow_html=True,
        )
        mc1, mc2, mc3, mc4 = st.columns(4)
        tr  = base_metrics["total_return"]
        shr = base_metrics["sharpe_ratio"]
        mdd = base_metrics["max_drawdown"]
        wr  = base_metrics["win_rate"]

        with mc1:
            c = "metric-positive" if tr >= 0 else "metric-negative"
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label-top'>Total Return</div>
                <div class='metric-value {c}'>{tr*100:+.1f}%</div>
                <div class='metric-sublabel'>{n_trades} trades</div>
            </div>""", unsafe_allow_html=True)

        with mc2:
            c = "metric-positive" if shr >= 1 else ("metric-negative" if shr < 0 else "metric-neutral")
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label-top'>Sharpe</div>
                <div class='metric-value {c}'>{shr:.2f}</div>
                <div class='metric-sublabel'>annualized, daily</div>
            </div>""", unsafe_allow_html=True)

        with mc3:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label-top'>Max Drawdown</div>
                <div class='metric-value metric-negative'>{mdd*100:.1f}%</div>
                <div class='metric-sublabel'>on equity</div>
            </div>""", unsafe_allow_html=True)

        with mc4:
            c = "metric-positive" if wr >= 0.5 else "metric-negative"
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label-top'>Win Rate</div>
                <div class='metric-value {c}'>{wr*100:.1f}%</div>
                <div class='metric-sublabel'>per-trade</div>
            </div>""", unsafe_allow_html=True)

    # ── Sensitivity Heatmap ──────────────────────────────────────────────────
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Sensitivity Heatmap</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>"
        "Maximum deviation from the base result, per (parameter, metric). "
        "<span style='color:rgba(34,197,94,0.9)'>■</span> Green = within 10%, "
        "<span style='color:rgba(6,182,212,0.8)'>■</span> teal = within 20%, "
        "<span style='color:rgba(245,158,11,0.8)'>■</span> amber = within 40%, "
        "<span style='color:rgba(239,68,68,0.8)'>■</span> red = beyond 40%."
        "</div>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        make_heatmap(heatmap_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # ── Per-Parameter Sweeps ─────────────────────────────────────────────────
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Per-Parameter Sweeps</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>"
        "Total return at each tested parameter value. "
        "Shaded band = ±10% of base result; dashed line = base value."
        "</div>",
        unsafe_allow_html=True,
    )

    chart_cols  = st.columns(2, gap="large")
    param_names = list(sweep_results.keys())

    for idx, pname in enumerate(param_names):
        with chart_cols[idx % 2]:
            fig = make_sensitivity_chart(
                sweep_results[pname], pname,
                base_params[pname], metric="total_return",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Parameter-by-Parameter Verdict ───────────────────────────────────────
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Parameter-by-Parameter Verdict</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>"
        "How much does total return swing as each parameter varies across its tested range?"
        "</div>",
        unsafe_allow_html=True,
    )

    card_cols = st.columns(2, gap="large")

    for idx, pname in enumerate(param_names):
        avg_score   = np.mean(list(per_param_scores[pname].values()))
        lbl, ck     = robustness_label(avg_score)
        lbl_color   = {"green": GREEN, "amber": AMBER, "red": RED}[ck]
        badge_bg    = {"green": "rgba(34,197,94,0.12)",
                       "amber": "rgba(245,158,11,0.12)",
                       "red":   "rgba(239,68,68,0.12)"}[ck]
        disp_name   = PARAM_DISPLAY.get(pname, pname)
        base_val    = base_params[pname]

        # Compute swing / best / worst from total_return column
        sdf       = sweep_results[pname]
        tr_series = sdf["total_return"].dropna()

        if len(tr_series) > 0:
            best_idx    = tr_series.idxmax()
            worst_idx   = tr_series.idxmin()
            best_param  = sdf.loc[best_idx,  "param_value"]
            worst_param = sdf.loc[worst_idx, "param_value"]
            best_ret    = tr_series[best_idx]
            worst_ret   = tr_series[worst_idx]
            swing       = (tr_series.max() - tr_series.min()) * 100

            if ck == "red":
                desc = (
                    f"Total return swings by <b>{swing:.0f}%</b> across the sweep. "
                    f"This is a <b>fragile knob</b> — small changes in the parameter "
                    f"meaningfully change the outcome, a red flag for overfitting."
                )
            elif ck == "amber":
                desc = (
                    f"Total return moves up to <b>{swing:.0f}%</b> across the sweep. "
                    f"Choose this parameter deliberately — results differ, but no value "
                    f"catastrophically breaks the strategy."
                )
            else:
                desc = (
                    f"Total return stays within <b>{swing:.0f}%</b> across the sweep. "
                    f"This parameter is <b>robust</b> — the strategy performs consistently "
                    f"regardless of the exact value chosen."
                )

            footer = (
                f"Best: {fmt_param_val(best_param)} ({best_ret*100:+.1f}%) · "
                f"Worst: {fmt_param_val(worst_param)} ({worst_ret*100:+.1f}%) · "
                f"Base: {fmt_param_val(base_val)}"
            )
        else:
            desc   = "No sweep data available."
            footer = ""

        with card_cols[idx % 2]:
            st.markdown(f"""
            <div style='background:#1a1c25;border:1px solid rgba(255,255,255,0.06);
                        border-left:3px solid {lbl_color};border-radius:8px;
                        padding:20px 24px;margin-bottom:14px;'>
                <div style='display:flex;justify-content:space-between;
                            align-items:flex-start;margin-bottom:12px;'>
                    <div style='display:flex;align-items:center;gap:10px;'>
                        <span style='font-family:IBM Plex Mono,monospace;font-size:10px;
                                     letter-spacing:0.1em;text-transform:uppercase;
                                     font-weight:600;color:{lbl_color};
                                     background:{badge_bg};padding:2px 9px;
                                     border-radius:3px;'>{lbl.upper()}</span>
                        <span style='font-family:IBM Plex Sans,sans-serif;font-size:15px;
                                     font-weight:600;color:#f1f5f9;'>{disp_name}</span>
                    </div>
                    <span style='font-family:IBM Plex Mono,monospace;font-size:30px;
                                 font-weight:700;color:{lbl_color};line-height:1;'>
                        {avg_score:.0f}
                    </span>
                </div>
                <div style='font-family:IBM Plex Sans,sans-serif;font-size:13px;
                            color:#9ca3af;line-height:1.65;margin-bottom:12px;'>
                    {desc}
                </div>
                <div style='font-family:IBM Plex Mono,monospace;font-size:11px;
                            color:#6b7280;'>{footer}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-family:IBM Plex Mono;font-size:11px;color:#374151;"
        f"text-align:center;border-top:1px solid rgba(255,255,255,0.04);"
        f"padding-top:24px'>Sensitivity Analysis Dashboard · {R['ticker']} · "
        f"Robustness scores based on coefficient of variation across parameter sweep"
        f"</div>",
        unsafe_allow_html=True,
    )

else:
    # ── Empty state ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style='display:flex;flex-direction:column;align-items:center;
                justify-content:center;min-height:480px;text-align:center;'>
        <div style='font-family:IBM Plex Mono;font-size:13px;letter-spacing:0.08em;
                    color:#4b5563;margin-bottom:16px;text-transform:uppercase;'>
            Ready to analyse
        </div>
        <div style='font-family:IBM Plex Sans;font-size:22px;color:#6b7280;
                    font-weight:300;max-width:480px;line-height:1.6;'>
            Configure parameters in the sidebar, then click
            <b style="color:#9ca3af">Run Analysis</b>
            to sweep the strategy across its parameter space.
        </div>
    </div>
    """, unsafe_allow_html=True)