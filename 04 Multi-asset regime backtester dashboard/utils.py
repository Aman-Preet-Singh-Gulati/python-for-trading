"""
utils.py
--------
Shared data, metrics, backtest-orchestration, and styling utilities for the
Multi-Asset Regime Backtester dashboard. The dashboard script
(multi_asset_dashboard.py) is intentionally a thin UI/plotting layer; the
actual data wrangling, walk-forward loop, and metric math live here, with
the HMM math itself delegated to hmm_utils.py.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

import hmm_utils

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Color identity
# ---------------------------------------------------------------------------

ASSET_COLORS: dict[str, str] = {
    "SPY": "#00d4ff",      # cyan
    "BTC-USD": "#f7931a",  # bitcoin orange
    "GLD": "#ffd700",      # gold
    "TLT": "#a78bfa",      # soft purple
}

# Extra distinct hues to cycle through for any ticker beyond the defaults.
EXTRA_PALETTE: list[str] = [
    "#4ade80",  # green
    "#fb7185",  # rose
    "#38bdf8",  # sky blue
    "#fbbf24",  # amber
    "#c084fc",  # violet
    "#2dd4bf",  # teal
    "#f472b6",  # pink
    "#84cc16",  # lime
]

# Two-state regime palette: index 0 = low-vol ("calm"), index 1 = high-vol
# ("turbulent"). A third, gray entry is used for the initial training
# segment, where there is no out-of-sample signal yet.
REGIME_COLORS: dict[int, str] = {
    0: "#34d399",   # calm / low-vol -> green-teal
    1: "#fb7185",   # turbulent / high-vol -> rose/red
    -1: "#3f3f4d",  # training period / no signal yet -> neutral gray
}
REGIME_LABELS: dict[int, str] = {
    0: "Low-Vol",
    1: "High-Vol",
    -1: "Training",
}

BACKGROUND_COLOR = "#0c0c14"
CARD_COLOR = "#141420"
MUTED_GRAY = "#7d7d8c"


def assign_asset_colors(tickers: list[str]) -> dict[str, str]:
    """Return a deterministic ticker -> hex color mapping. Defaults keep
    their fixed identity colors; any other ticker cycles through the
    extra palette, skipping colors already in use."""
    used = set(ASSET_COLORS.values())
    mapping = {}
    palette_cycle = [c for c in EXTRA_PALETTE if c not in used] or EXTRA_PALETTE
    extra_i = 0
    for t in tickers:
        if t in ASSET_COLORS:
            mapping[t] = ASSET_COLORS[t]
        else:
            mapping[t] = palette_cycle[extra_i % len(palette_cycle)]
            extra_i += 1
    return mapping


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# ---------------------------------------------------------------------------
# CSS injection -- the "world shifts color" effect
# ---------------------------------------------------------------------------

def inject_css(accent: str) -> str:
    """Return a <style> block tying the whole dashboard's accent to
    `accent` (the currently selected asset's color). Call again on every
    rerun with the newly selected asset's color."""
    accent_soft = hex_to_rgba(accent, 0.15)
    accent_glow = hex_to_rgba(accent, 0.45)
    accent_border = hex_to_rgba(accent, 0.35)
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap');

:root {{
    --accent: {accent};
    --accent-soft: {accent_soft};
    --accent-glow: {accent_glow};
    --accent-border: {accent_border};
    --bg: {BACKGROUND_COLOR};
    --card: {CARD_COLOR};
}}

.stApp {{
    background-color: var(--bg) !important;
}}

h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
    font-family: 'Outfit', sans-serif !important;
    letter-spacing: -0.01em;
}}

body, .stMarkdown, p, span, label, div {{
    font-family: 'Outfit', sans-serif;
}}

/* numbers / metrics in monospace-style Fira Code */
[data-testid="stMetricValue"], .mono-num, code {{
    font-family: 'Fira Code', monospace !important;
}}

[data-testid="stMetric"] {{
    background-color: var(--card);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 0.6rem 0.9rem;
}}

[data-testid="stSidebar"] {{
    background-color: #0a0a10;
    border-right: 1px solid rgba(255,255,255,0.05);
}}

.regime-card, .glass-card {{
    background-color: var(--card);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}}

.glow-border {{
    border: 1px solid var(--accent) !important;
    box-shadow: 0 0 18px var(--accent-glow);
}}

a.asset-pill {{
    display: inline-block;
    text-decoration: none !important;
    border-radius: 999px;
    padding: 10px 18px;
    margin: 4px 6px 4px 0;
    font-weight: 600;
    font-size: 0.92rem;
    transition: all 0.15s ease-in-out;
}}

::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-thumb {{ background: var(--accent-border); border-radius: 8px; }}

.stButton > button {{
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.08);
    background-color: var(--card);
    color: #e5e5ee;
}}
.stButton > button:hover {{
    border-color: var(--accent);
    color: var(--accent);
}}

hr {{ border-color: rgba(255,255,255,0.08); }}
</style>
"""


# ---------------------------------------------------------------------------
# Data download
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=3600)
def download_price_series(ticker: str, start: str, end: str) -> Optional[pd.Series]:
    """Download daily close prices for a single ticker via yfinance.
    Returns None on failure / empty result so callers can show a friendly
    warning instead of crashing. Cached per (ticker, start, end)."""
    try:
        df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if df is None or df.empty:
            return None
        close = df["Close"]
        if isinstance(close, pd.DataFrame):  # safety for odd column shapes
            close = close.iloc[:, 0]
        close = close.dropna()
        close.index = pd.DatetimeIndex(close.index).tz_localize(None)
        return close if len(close) > 0 else None
    except Exception:
        return None


def compute_log_returns(prices: pd.Series) -> pd.Series:
    return np.log(prices / prices.shift(1)).dropna()


# ---------------------------------------------------------------------------
# Performance metrics
# ---------------------------------------------------------------------------

def sharpe_ratio(returns: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    returns = returns.dropna()
    if len(returns) < 2:
        return np.nan
    excess = returns - rf / periods_per_year
    std = excess.std()
    if std == 0 or np.isnan(std):
        return np.nan
    return float(excess.mean() / std * np.sqrt(periods_per_year))


def equity_curve_from_returns(returns: pd.Series, start_value: float = 1.0) -> pd.Series:
    return start_value * (1 + returns.fillna(0)).cumprod()


def max_drawdown(equity: pd.Series) -> float:
    if len(equity) == 0:
        return np.nan
    running_max = equity.cummax()
    dd = equity / running_max - 1.0
    return float(dd.min())


def total_return(equity: pd.Series) -> float:
    if len(equity) < 2:
        return np.nan
    return float(equity.iloc[-1] / equity.iloc[0] - 1.0)


def cagr(equity: pd.Series, periods_per_year: int = 252) -> float:
    if len(equity) < 2:
        return np.nan
    n_periods = len(equity)
    growth = equity.iloc[-1] / equity.iloc[0]
    if growth <= 0:
        return np.nan
    return float(growth ** (periods_per_year / n_periods) - 1.0)


# ---------------------------------------------------------------------------
# Trend-following benchmark
# ---------------------------------------------------------------------------

def sma_trend_returns(prices: pd.Series, returns: pd.Series, window: int = 200) -> pd.Series:
    """Long-only 200-day SMA trend benchmark: hold the asset whenever
    yesterday's close was above yesterday's SMA, otherwise sit in cash
    (0% return). The signal is lagged by one day so it never uses the
    same day's return to decide that day's position."""
    sma = prices.rolling(window, min_periods=window).mean()
    signal = (prices > sma).astype(float)
    signal = signal.shift(1).reindex(returns.index).fillna(0.0)
    return signal * returns


# ---------------------------------------------------------------------------
# Walk-forward windowing
# ---------------------------------------------------------------------------

def walk_forward_windows(dates: pd.DatetimeIndex, train_months: int = 12, test_months: int = 6):
    """Generate (train_start, train_end, test_start, test_end) timestamp
    tuples covering a rolling, fixed-length train window followed by a
    test window, sliding forward by `test_months` each step so test
    segments are contiguous and non-overlapping."""
    dates = pd.DatetimeIndex(dates).sort_values()
    if len(dates) == 0:
        return []
    start, end = dates[0], dates[-1]
    windows = []
    train_start = start
    guard = 0
    while guard < 500:
        guard += 1
        train_end = train_start + pd.DateOffset(months=train_months)
        test_start = train_end
        test_end = test_start + pd.DateOffset(months=test_months)
        if test_start >= end:
            break
        actual_test_end = min(test_end, end)
        windows.append((train_start, train_end, test_start, actual_test_end))
        if actual_test_end >= end:
            break
        train_start = train_start + pd.DateOffset(months=test_months)
    return windows


# ---------------------------------------------------------------------------
# Walk-forward regime backtest orchestration
# ---------------------------------------------------------------------------

@dataclass
class BacktestResult:
    ticker: str
    ok: bool
    message: str = ""
    oos_index: pd.DatetimeIndex = field(default_factory=lambda: pd.DatetimeIndex([]))
    strategy_returns: pd.Series = field(default_factory=pd.Series)
    buyhold_returns: pd.Series = field(default_factory=pd.Series)
    sma_returns: pd.Series = field(default_factory=pd.Series)
    regime: pd.Series = field(default_factory=pd.Series)   # causal regime per oos day (0/1)
    full_prices: pd.Series = field(default_factory=pd.Series)
    full_returns: pd.Series = field(default_factory=pd.Series)
    n_windows: int = 0
    last_model: object = None  # most recent window's fitted hmm_utils.GaussianHMM, for diagnostics


MIN_TRAIN_OBS = 60  # minimum trading days required to attempt an HMM fit


def run_walk_forward_backtest(
    ticker: str,
    prices: pd.Series,
    train_months: int = 12,
    test_months: int = 6,
    alloc_low: float = 0.95,
    alloc_high: float = 0.60,
    sma_window: int = 200,
) -> BacktestResult:
    if prices is None or len(prices) < 80:
        return BacktestResult(ticker, ok=False, message="Not enough price history downloaded.")

    returns = compute_log_returns(prices)
    if len(returns) < MIN_TRAIN_OBS * 2:
        return BacktestResult(ticker, ok=False, message="Not enough return history for a train+test split.")

    windows = walk_forward_windows(returns.index, train_months, test_months)
    if len(windows) == 0:
        return BacktestResult(
            ticker, ok=False,
            message="Date range too short for the chosen train/test window sizes.",
        )

    # causal regime label for every day that ever appears in a test segment,
    # plus we track the very last train-segment regime to seed day-1 of the
    # very first test segment.
    regime_full = pd.Series(index=returns.index, dtype=float)
    strategy_ret_parts = []
    last_seed_regime = 0  # default to low-vol if we have nothing yet

    n_windows_used = 0
    last_model = None
    for train_start, train_end, test_start, test_end in windows:
        train_mask = (returns.index >= train_start) & (returns.index < train_end)
        test_mask = (returns.index >= test_start) & (returns.index <= test_end)
        train_r = returns[train_mask]
        test_r = returns[test_mask]
        if len(train_r) < MIN_TRAIN_OBS or len(test_r) == 0:
            continue

        try:
            result = hmm_utils.fit_and_label_regimes(train_r.values, test_r.values)
        except Exception:
            continue

        n_windows_used += 1
        last_model = result["model"]
        test_regime_arr = result["test_regime"]
        test_idx = test_r.index
        regime_full.loc[test_idx] = test_regime_arr

        # causal sequence for THIS window: [train_regime..., test_regime...]
        combined_regime = np.concatenate([result["train_regime"], test_regime_arr])
        # position for day i depends on the regime AS OF i-1 (lag 1, no peeking)
        lagged = np.empty_like(combined_regime)
        lagged[0] = last_seed_regime
        lagged[1:] = combined_regime[:-1]
        lagged_test = lagged[len(train_r):]

        alloc_map = {0: alloc_low, 1: alloc_high}
        positions = np.array([alloc_map.get(s, alloc_low) for s in lagged_test])
        strat_ret = pd.Series(positions * test_r.values, index=test_idx)
        strategy_ret_parts.append(strat_ret)

        last_seed_regime = int(combined_regime[-1])

    if n_windows_used == 0 or len(strategy_ret_parts) == 0:
        return BacktestResult(ticker, ok=False, message="HMM fit failed on every walk-forward window.")

    strategy_returns = pd.concat(strategy_ret_parts).sort_index()
    strategy_returns = strategy_returns[~strategy_returns.index.duplicated(keep="first")]

    oos_index = strategy_returns.index
    buyhold_returns = returns.reindex(oos_index)
    sma_full = sma_trend_returns(prices, returns, window=sma_window)
    sma_returns = sma_full.reindex(oos_index).fillna(0.0)
    regime_oos = regime_full.reindex(oos_index)

    return BacktestResult(
        ticker=ticker,
        ok=True,
        oos_index=oos_index,
        strategy_returns=strategy_returns,
        buyhold_returns=buyhold_returns,
        sma_returns=sma_returns,
        regime=regime_oos,
        full_prices=prices,
        full_returns=returns,
        n_windows=n_windows_used,
        last_model=last_model,
    )


# ---------------------------------------------------------------------------
# Stress periods
# ---------------------------------------------------------------------------

STRESS_PERIODS: dict[str, tuple[str, str]] = {
    "2008 GFC": ("2008-09-01", "2009-03-31"),
    "2020 COVID": ("2020-02-01", "2020-04-30"),
    "2022 Bear": ("2022-01-01", "2022-10-31"),
}


def slice_window(series: pd.Series, start: str, end: str) -> pd.Series:
    if series is None or len(series) == 0:
        return pd.Series(dtype=float)
    mask = (series.index >= pd.Timestamp(start)) & (series.index <= pd.Timestamp(end))
    return series[mask]


def stress_metrics(returns: pd.Series, start: str, end: str) -> Optional[dict]:
    """Cumulative return + max drawdown for `returns` restricted to a
    crisis window. Returns None if there's no data covering that window
    (e.g. BTC-USD has no 2008 history)."""
    window_returns = slice_window(returns, start, end)
    if len(window_returns) < 3:
        return None
    eq = equity_curve_from_returns(window_returns)
    return {
        "cum_return": total_return(eq),
        "max_drawdown": max_drawdown(eq),
        "n_days": len(window_returns),
    }


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_pct(x: float, decimals: int = 1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x * 100:.{decimals}f}%"


def fmt_signed_pct(x: float, decimals: int = 1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    sign = "+" if x >= 0 else ""
    return f"{sign}{x * 100:.{decimals}f}%"


def fmt_num(x: float, decimals: int = 2) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:.{decimals}f}"