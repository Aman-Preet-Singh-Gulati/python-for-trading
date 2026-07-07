"""
multi_asset_dashboard.py
-------------------------
Multi-Asset Regime Backtester -- a Streamlit dashboard that fits a 2-state
Gaussian HMM (low-vol / high-vol) per asset, runs a walk-forward backtest
(1yr train / 6mo test by default) that scales exposure down in high-vol
regimes, and compares the result against buy-and-hold and 200-day SMA
trend-following benchmarks -- including dedicated stress-test windows for
2008, 2020, and 2022.

The whole UI re-themes itself around whichever asset's tab is selected:
chart lines, grid color, glow borders, and the regime-strip key colors all
shift to that asset's identity color.

Run with:  streamlit run multi_asset_dashboard.py
"""

from datetime import date, datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import hmm_utils
import utils

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Multi-Asset Regime Backtester",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_TICKERS = ["SPY", "BTC-USD", "GLD", "TLT"]

if "selected_asset" not in st.session_state:
    st.session_state.selected_asset = DEFAULT_TICKERS[0]
if "results" not in st.session_state:
    st.session_state.results = None
if "tickers_run" not in st.session_state:
    st.session_state.tickers_run = []


def _select_asset(ticker: str) -> None:
    st.session_state.selected_asset = ticker


# ---------------------------------------------------------------------------
# Sidebar -- configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚙️ Backtest configuration")

    tickers_raw = st.text_input(
        "Assets (comma-separated tickers)",
        value=",".join(DEFAULT_TICKERS),
        help="Use any Yahoo Finance ticker, e.g. SPY, BTC-USD, GLD, TLT, QQQ, EFA…",
    )
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    seen = set()
    tickers = [t for t in tickers if not (t in seen or seen.add(t))]  # de-dupe, keep order

    st.markdown("##### Date range")
    col_a, col_b = st.columns(2)
    with col_a:
        start_date = st.date_input(
            "Start", value=date(2006, 1, 1), min_value=date(1990, 1, 1), max_value=date.today()
        )
    with col_b:
        end_date = st.date_input("End", value=date.today(), min_value=date(1990, 1, 1), max_value=date.today())
    st.caption(
        "Default start is 2006 (not just 5 years back) so the 2008 stress "
        "test has data to work with. Newer assets like BTC-USD simply won't "
        "have data before their listing date -- that's handled gracefully."
    )

    st.markdown("##### Walk-forward window")
    col_c, col_d = st.columns(2)
    with col_c:
        train_months = st.number_input("Train (months)", min_value=3, max_value=36, value=12, step=1)
    with col_d:
        test_months = st.number_input("Test (months)", min_value=1, max_value=24, value=6, step=1)

    with st.expander("Advanced: allocation & trend settings"):
        alloc_low_pct = st.slider("Low-vol regime allocation (%)", 0, 100, 95, step=5)
        alloc_high_pct = st.slider("High-vol regime allocation (%)", 0, 100, 60, step=5)
        sma_window = st.number_input("SMA trend window (days)", min_value=20, max_value=300, value=200, step=10)

    run_clicked = st.button("🚀 Run Backtest", type="primary", use_container_width=True)

    if run_clicked:
        if len(tickers) == 0:
            st.error("Add at least one ticker.")
        elif start_date >= end_date:
            st.error("Start date must be before end date.")
        else:
            progress = st.progress(0.0, text="Starting…")
            results = {}
            start_str, end_str = start_date.isoformat(), end_date.isoformat()
            for i, t in enumerate(tickers):
                progress.progress(i / len(tickers), text=f"Downloading {t}…")
                prices = utils.download_price_series(t, start_str, end_str)
                progress.progress((i + 0.5) / len(tickers), text=f"Fitting HMM regimes: {t}…")
                res = utils.run_walk_forward_backtest(
                    t,
                    prices,
                    train_months=train_months,
                    test_months=test_months,
                    alloc_low=alloc_low_pct / 100,
                    alloc_high=alloc_high_pct / 100,
                    sma_window=sma_window,
                )
                results[t] = res
                progress.progress((i + 1) / len(tickers), text=f"Done: {t}")
            progress.empty()
            st.session_state.results = results
            st.session_state.tickers_run = tickers
            if st.session_state.selected_asset not in results:
                st.session_state.selected_asset = tickers[0]
            n_ok = sum(1 for r in results.values() if r.ok)
            if n_ok == 0:
                st.error("No asset produced a valid backtest. Check tickers / date range.")
            else:
                st.success(f"Backtest complete: {n_ok}/{len(tickers)} asset(s) ready.")

    st.markdown("---")
    st.caption(
        "Built with a from-scratch Gaussian HMM (Baum-Welch fit, scaled "
        "log-domain forward algorithm for causal, look-ahead-free regime "
        "filtering during the walk-forward test windows)."
    )

# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------

results = st.session_state.results

if results is None:
    st.markdown(utils.inject_css(utils.ASSET_COLORS["SPY"]), unsafe_allow_html=True)
    st.title("🌐 Multi-Asset Regime Backtester")
    st.markdown(
        "<div class='glass-card'>"
        "Configure your assets, date range, and walk-forward window in the "
        "sidebar, then hit <b>Run Backtest</b>. Each asset gets its own "
        "2-state Gaussian HMM (low-vol / high-vol), a walk-forward "
        "backtest that scales exposure down in turbulent regimes, and a "
        "head-to-head comparison against buy-and-hold and 200-day SMA "
        "trend-following -- plus dedicated 2008 / 2020 / 2022 stress tests."
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

tickers_run = st.session_state.tickers_run
colors = utils.assign_asset_colors(tickers_run)

selected = st.session_state.selected_asset
if selected not in results:
    selected = tickers_run[0]
    st.session_state.selected_asset = selected
accent = colors[selected]

# ---------------------------------------------------------------------------
# Theming -- the whole dashboard tints to the selected asset's color
# ---------------------------------------------------------------------------

pill_css = ["<style>"]
for t in tickers_run:
    c = colors[t]
    is_active = t == selected
    bg = c if is_active else utils.hex_to_rgba(c, 0.16)
    text_color = "#0a0a10" if is_active else c
    border = c if is_active else utils.hex_to_rgba(c, 0.35)
    glow = f"box-shadow: 0 0 22px {utils.hex_to_rgba(c, 0.55)};" if is_active else "box-shadow:none;"
    pill_css.append(
        f"""
        .st-key-pill_{t} {{
            background-color: {bg};
            border: 1.5px solid {border};
            border-radius: 16px;
            padding: 2px 6px 8px 6px;
            margin-bottom: 6px;
            {glow}
            transition: all 0.15s ease-in-out;
        }}
        .st-key-pill_{t} button {{
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: {text_color} !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
            width: 100%;
        }}
        .st-key-pill_{t} button:hover {{
            color: {text_color} !important;
            opacity: 0.85;
        }}
        .st-key-pillsub_{t} p {{
            color: {text_color if is_active else utils.hex_to_rgba(c, 0.85)} !important;
            text-align: center;
            font-family: 'Fira Code', monospace !important;
            font-size: 0.74rem !important;
            margin-top: -10px;
            opacity: {1.0 if is_active else 0.9};
        }}
        """
    )
pill_css.append("</style>")

st.markdown(utils.inject_css(accent), unsafe_allow_html=True)
st.markdown("".join(pill_css), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header + asset pill selector
# ---------------------------------------------------------------------------

st.markdown(
    f"<h1 style='margin-bottom:0;'>🌐 Multi-Asset Regime Backtester</h1>"
    f"<p style='color:{accent}; font-weight:600; margin-top:0;'>"
    f"Currently exploring &nbsp;{selected}&nbsp;'s color world</p>",
    unsafe_allow_html=True,
)

quick_stats = {}
for t in tickers_run:
    r = results.get(t)
    if r is None or not r.ok:
        quick_stats[t] = None
        continue
    strat_eq = utils.equity_curve_from_returns(r.strategy_returns)
    bh_eq = utils.equity_curve_from_returns(r.buyhold_returns)
    strat_sharpe = utils.sharpe_ratio(r.strategy_returns)
    bh_sharpe = utils.sharpe_ratio(r.buyhold_returns)
    quick_stats[t] = {
        "ret": utils.total_return(strat_eq),
        "sharpe_delta": (strat_sharpe - bh_sharpe) if not (np.isnan(strat_sharpe) or np.isnan(bh_sharpe)) else np.nan,
    }

pill_cols = st.columns(len(tickers_run))
for i, t in enumerate(tickers_run):
    with pill_cols[i]:
        with st.container(key=f"pill_{t}"):
            st.button(t, key=f"btn_{t}", on_click=_select_asset, args=(t,), use_container_width=True)
            qs = quick_stats.get(t)
            with st.container(key=f"pillsub_{t}"):
                if qs is None:
                    st.caption("no data")
                else:
                    arrow = "↑" if qs["sharpe_delta"] >= 0 else "↓"
                    st.caption(f"{utils.fmt_signed_pct(qs['ret'])} · Sharpe {arrow}{utils.fmt_num(abs(qs['sharpe_delta']))}")

st.markdown("---")

res = results.get(selected)

if res is None or not res.ok:
    st.warning(f"**{selected}**: {res.message if res else 'No result.'}")
else:
    # -----------------------------------------------------------------
    # Hero chart -- equity curves
    # -----------------------------------------------------------------
    strat_eq = utils.equity_curve_from_returns(res.strategy_returns)
    bh_eq = utils.equity_curve_from_returns(res.buyhold_returns)
    sma_eq = utils.equity_curve_from_returns(res.sma_returns)

    strat_sharpe = utils.sharpe_ratio(res.strategy_returns)
    bh_sharpe = utils.sharpe_ratio(res.buyhold_returns)
    sma_sharpe = utils.sharpe_ratio(res.sma_returns)
    sharpe_delta = strat_sharpe - bh_sharpe if not (np.isnan(strat_sharpe) or np.isnan(bh_sharpe)) else np.nan

    metric_cols = st.columns(4)
    metric_cols[0].metric(f"{selected} Regime Strategy", utils.fmt_pct(utils.total_return(strat_eq)))
    metric_cols[1].metric("Buy & Hold", utils.fmt_pct(utils.total_return(bh_eq)))
    metric_cols[2].metric("Strategy Sharpe", utils.fmt_num(strat_sharpe))
    metric_cols[3].metric(
        "Sharpe vs Buy & Hold",
        utils.fmt_num(strat_sharpe),
        delta=f"{sharpe_delta:+.2f}",
    )

    grid_color = utils.hex_to_rgba(accent, 0.07)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=strat_eq.index, y=strat_eq.values, name=f"{selected} Regime Strategy",
            line=dict(color=accent, width=3.2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=bh_eq.index, y=bh_eq.values, name="Buy & Hold",
            line=dict(color=utils.MUTED_GRAY, width=2, dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=sma_eq.index, y=sma_eq.values, name="200-day SMA Trend",
            line=dict(color="rgba(170,170,195,0.55)", width=1.4, dash="dot"),
        )
    )
    fig.update_layout(
        paper_bgcolor=utils.BACKGROUND_COLOR,
        plot_bgcolor=utils.BACKGROUND_COLOR,
        font=dict(color="#e7e7f0", family="Outfit, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=40, b=10),
        height=440,
        xaxis=dict(gridcolor=grid_color, zeroline=False),
        yaxis=dict(gridcolor=grid_color, zeroline=False, title="Growth of $1 (out-of-sample)"),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander(f"🔬 HMM diagnostics for {selected} (most recent walk-forward window)"):
        model: hmm_utils.GaussianHMM = res.last_model
        if model is not None:
            diag_cols = st.columns(2)
            ann_vol = np.sqrt(np.maximum(model.vars_, 0)) * np.sqrt(252) * 100
            diag_cols[0].markdown(
                f"**Low-Vol state** — mean daily return {model.means_[0]*100:.3f}%, "
                f"annualized vol ≈ {ann_vol[0]:.1f}%"
            )
            diag_cols[1].markdown(
                f"**High-Vol state** — mean daily return {model.means_[1]*100:.3f}%, "
                f"annualized vol ≈ {ann_vol[1]:.1f}%"
            )
            st.caption(
                f"Persistence (probability of staying in the same regime next day): "
                f"Low-Vol {model.transmat_[0,0]*100:.1f}%, High-Vol {model.transmat_[1,1]*100:.1f}%. "
                f"Fitted across {res.n_windows} walk-forward windows; figures shown are from the "
                f"most recent one ({model.n_iter_run_} EM iterations to converge)."
            )
        else:
            st.caption("No fitted model available.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Regime timeline strips -- all assets, stacked
# ---------------------------------------------------------------------------

st.markdown("### 📊 Regime Timeline — all assets")
st.caption(
    "Each row is one asset's out-of-sample regime path. "
    f"<span style='color:{utils.REGIME_COLORS[0]}'>■ Low-Vol</span> &nbsp; "
    f"<span style='color:{utils.REGIME_COLORS[1]}'>■ High-Vol</span> &nbsp; "
    f"<span style='color:#9a9aa8'>■ Training (no signal yet)</span> &nbsp; "
    "blank = no data for that asset yet.",
    unsafe_allow_html=True,
)

valid_assets = [t for t in tickers_run if results.get(t) and results[t].ok]

if len(valid_assets) == 0:
    st.info("No valid backtests to show on the regime timeline.")
else:
    all_dates = pd.DatetimeIndex(sorted(set().union(*[results[t].full_returns.index for t in valid_assets])))
    z = np.full((len(valid_assets), len(all_dates)), np.nan)
    date_pos = {d: i for i, d in enumerate(all_dates)}

    for row, t in enumerate(valid_assets):
        r = results[t]
        # training period (no oos signal yet): mark every day in full_returns
        # that comes before this asset's own out-of-sample start as -1
        if len(r.oos_index) > 0:
            oos_start = r.oos_index.min()
            train_days = r.full_returns.index[r.full_returns.index < oos_start]
            for d in train_days:
                z[row, date_pos[d]] = -1
        for d, val in r.regime.dropna().items():
            z[row, date_pos[d]] = val

    n_rows = len(valid_assets)
    fig_strip = go.Figure(
        data=go.Heatmap(
            z=z,
            x=all_dates,
            y=valid_assets,
            zmin=-1,
            zmax=1,
            colorscale=[
                [0.0, utils.REGIME_COLORS[-1]],
                [0.5, utils.REGIME_COLORS[0]],
                [1.0, utils.REGIME_COLORS[1]],
            ],
            showscale=False,
            hoverongaps=False,
            hovertemplate="%{y} · %{x|%Y-%m-%d}<extra></extra>",
            xgap=0,
            ygap=4,
        )
    )
    annotations = []
    for t in valid_assets:
        annotations.append(
            dict(
                xref="paper", x=-0.012, xanchor="right",
                yref="y", y=t, yanchor="middle",
                text=f"<b>{t}</b>", showarrow=False,
                font=dict(color=colors[t], size=13, family="Outfit, sans-serif"),
            )
        )
    fig_strip.update_layout(
        paper_bgcolor=utils.BACKGROUND_COLOR,
        plot_bgcolor=utils.BACKGROUND_COLOR,
        font=dict(color="#e7e7f0"),
        height=max(140, 38 * n_rows + 70),
        margin=dict(l=90, r=20, t=20, b=30),
        yaxis=dict(showticklabels=False, showgrid=False),
        xaxis=dict(showgrid=False),
        annotations=annotations,
    )
    st.plotly_chart(fig_strip, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Comparison table -- ranked by Sharpe improvement
# ---------------------------------------------------------------------------

st.markdown("### 🏆 Asset comparison — ranked by Sharpe improvement over Buy & Hold")

rows = []
for t in tickers_run:
    r = results.get(t)
    if r is None or not r.ok:
        continue
    s_eq = utils.equity_curve_from_returns(r.strategy_returns)
    b_eq = utils.equity_curve_from_returns(r.buyhold_returns)
    s_sharpe = utils.sharpe_ratio(r.strategy_returns)
    b_sharpe = utils.sharpe_ratio(r.buyhold_returns)
    delta = s_sharpe - b_sharpe if not (np.isnan(s_sharpe) or np.isnan(b_sharpe)) else np.nan
    rows.append(
        {
            "Ticker": t,
            "Strategy Return": utils.total_return(s_eq),
            "Buy&Hold Return": utils.total_return(b_eq),
            "Strategy Sharpe": s_sharpe,
            "B&H Sharpe": b_sharpe,
            "Sharpe Improvement": delta,
            "Strategy MaxDD": utils.max_drawdown(s_eq),
            "B&H MaxDD": utils.max_drawdown(b_eq),
            "Windows": r.n_windows,
        }
    )

if len(rows) == 0:
    st.info("No completed backtests yet.")
else:
    table_df = pd.DataFrame(rows).sort_values("Sharpe Improvement", ascending=False).reset_index(drop=True)
    best_ticker = table_df.iloc[0]["Ticker"]

    html = ["<div style='overflow-x:auto;'>"]
    html.append(
        "<table style='width:100%; border-collapse:separate; border-spacing:0 6px; font-family:Outfit,sans-serif;'>"
    )
    html.append(
        "<tr style='color:#9a9aa8; font-size:0.82rem; text-align:left;'>"
        "<th style='padding:6px 10px;'>Asset</th>"
        "<th style='padding:6px 10px;'>Strategy Return</th>"
        "<th style='padding:6px 10px;'>B&amp;H Return</th>"
        "<th style='padding:6px 10px;'>Strategy Sharpe</th>"
        "<th style='padding:6px 10px;'>B&amp;H Sharpe</th>"
        "<th style='padding:6px 10px;'>Sharpe Improvement</th>"
        "<th style='padding:6px 10px;'>Strategy MaxDD</th>"
        "<th style='padding:6px 10px;'>B&amp;H MaxDD</th>"
        "<th style='padding:6px 10px;'>Windows</th>"
        "</tr>"
    )
    for _, row in table_df.iterrows():
        t = row["Ticker"]
        c = colors.get(t, utils.MUTED_GRAY)
        is_best = t == best_ticker
        row_style = (
            f"background:{utils.hex_to_rgba(c, 0.08)}; box-shadow: inset 0 0 0 1.5px {c};"
            if is_best
            else "background:#141420;"
        )
        improvement = row["Sharpe Improvement"]
        if pd.isna(improvement):
            imp_html = "<span style='color:#9a9aa8'>—</span>"
        elif improvement >= 0:
            imp_html = f"<span style='color:#34d399; font-family:Fira Code, monospace;'>↑ +{improvement:.2f}</span>"
        else:
            imp_html = f"<span style='color:#fb7185; font-family:Fira Code, monospace;'>↓ {improvement:.2f}</span>"
        trophy = " 🏆" if is_best else ""
        html.append(
            f"<tr style='{row_style} border-radius:10px; font-family:Fira Code, monospace; font-size:0.88rem;'>"
            f"<td style='padding:8px 10px; font-weight:700; color:{c}; font-family:Outfit, sans-serif;'>{t}{trophy}</td>"
            f"<td style='padding:8px 10px;'>{utils.fmt_signed_pct(row['Strategy Return'])}</td>"
            f"<td style='padding:8px 10px;'>{utils.fmt_signed_pct(row['Buy&Hold Return'])}</td>"
            f"<td style='padding:8px 10px;'>{utils.fmt_num(row['Strategy Sharpe'])}</td>"
            f"<td style='padding:8px 10px;'>{utils.fmt_num(row['B&H Sharpe'])}</td>"
            f"<td style='padding:8px 10px;'>{imp_html}</td>"
            f"<td style='padding:8px 10px;'>{utils.fmt_pct(row['Strategy MaxDD'])}</td>"
            f"<td style='padding:8px 10px;'>{utils.fmt_pct(row['B&H MaxDD'])}</td>"
            f"<td style='padding:8px 10px; color:#9a9aa8;'>{int(row['Windows'])}</td>"
            f"</tr>"
        )
    html.append("</table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Stress test section
# ---------------------------------------------------------------------------

st.markdown("### 🧪 Stress tests")
st.caption("Strategy vs Buy & Hold maximum drawdown inside each crisis window. Bars are omitted for assets with no price history covering that period.")

stress_cols = st.columns(3)
for col, (label, (start, end)) in zip(stress_cols, utils.STRESS_PERIODS.items()):
    with col:
        st.markdown(f"**{label}**")
        bar_assets, strat_vals, bh_vals, bar_colors = [], [], [], []
        skipped = []
        for t in tickers_run:
            r = results.get(t)
            if r is None or not r.ok:
                continue
            bh_metrics = utils.stress_metrics(r.full_returns, start, end)
            if bh_metrics is None:
                skipped.append(t)
                continue
            strat_metrics = utils.stress_metrics(r.strategy_returns, start, end)
            bar_assets.append(t)
            bh_vals.append(bh_metrics["max_drawdown"] * 100)
            strat_vals.append((strat_metrics["max_drawdown"] * 100) if strat_metrics else 0.0)
            bar_colors.append(colors.get(t, utils.MUTED_GRAY))

        if len(bar_assets) == 0:
            st.info("No assets have data for this period.")
        else:
            fig_s = go.Figure()
            fig_s.add_trace(
                go.Bar(
                    y=bar_assets, x=strat_vals, name="Strategy", orientation="h",
                    marker_color=bar_colors, opacity=0.95,
                )
            )
            fig_s.add_trace(
                go.Bar(
                    y=bar_assets, x=bh_vals, name="Buy & Hold", orientation="h",
                    marker_color=utils.MUTED_GRAY, opacity=0.7,
                )
            )
            fig_s.update_layout(
                barmode="group",
                paper_bgcolor=utils.BACKGROUND_COLOR,
                plot_bgcolor=utils.BACKGROUND_COLOR,
                font=dict(color="#e7e7f0", size=11),
                margin=dict(l=10, r=10, t=10, b=10),
                height=110 + 38 * len(bar_assets),
                xaxis=dict(title="Max drawdown (%)", gridcolor="rgba(255,255,255,0.06)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, font=dict(size=10)),
            )
            st.plotly_chart(fig_s, use_container_width=True)
        if skipped:
            st.caption(f"No data: {', '.join(skipped)}")

st.markdown("---")
st.caption(
    "Educational tool, not investment advice. Past regime classification does not guarantee "
    "future performance; the HMM and allocation rule are deliberately simple."
)