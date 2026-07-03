"""
utils.py — Backtest engine and robustness scoring for the Sensitivity Dashboard.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from dataclasses import dataclass
from typing import Dict, List, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# Data fetching
# ──────────────────────────────────────────────────────────────────────────────

def fetch_price_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download adjusted-close daily prices for *ticker* between *start* and *end*."""
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for {ticker} between {start} and {end}.")
    df = df[["Close"]].rename(columns={"Close": "close"})
    df.index = pd.to_datetime(df.index)
    df = df.dropna()
    # Flatten MultiIndex columns if present (yfinance >= 0.2.x)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Strategy: SMA crossover
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class BacktestResult:
    total_return: float       # e.g. 0.35 → 35 %
    sharpe_ratio: float
    max_drawdown: float       # e.g. −0.18 → −18 %
    win_rate: float           # e.g. 0.55 → 55 %
    equity_curve: pd.Series   # indexed by date


def run_sma_crossover(
    prices: pd.DataFrame,
    fast_ma: int,
    slow_ma: int,
    stop_loss_pct: float,
    take_profit_pct: float,
) -> BacktestResult:
    """
    Simple SMA crossover strategy with per-trade stop-loss and take-profit.

    Rules
    -----
    - Long when fast_ma crosses above slow_ma; exit when it crosses below,
      or when stop/take-profit is hit.
    - Fully-invested (100 % of capital) per trade, no short side.
    """
    close = prices["close"].copy()

    fast = close.rolling(fast_ma).mean()
    slow = close.rolling(slow_ma).mean()

    signal = (fast > slow).astype(int)
    signal_shifted = signal.shift(1).fillna(0)

    # Daily log returns
    log_ret = np.log(close / close.shift(1)).fillna(0)

    # ── Trade-level simulation ──────────────────────────────────────────────
    in_trade = False
    entry_price = 0.0
    equity = 1.0
    equity_series = []
    trade_returns = []

    stop = stop_loss_pct / 100.0
    take = take_profit_pct / 100.0

    position_daily_returns = []

    for i in range(len(close)):
        date = close.index[i]
        price = close.iloc[i]

        if not in_trade:
            if signal_shifted.iloc[i] == 1:
                # Enter long
                in_trade = True
                entry_price = price
                position_daily_returns.append(0.0)
            else:
                position_daily_returns.append(0.0)
        else:
            # Daily P&L vs entry
            pct_from_entry = (price - entry_price) / entry_price

            # Check stop / take-profit or signal exit
            if pct_from_entry <= -stop:
                # Stop hit — cap loss at stop level
                trade_ret = -stop
                in_trade = False
                trade_returns.append(trade_ret)
                position_daily_returns.append(trade_ret)  # simplified: single-bar exit
                continue
            elif pct_from_entry >= take:
                trade_ret = take
                in_trade = False
                trade_returns.append(trade_ret)
                position_daily_returns.append(trade_ret)
                continue
            elif signal_shifted.iloc[i] == 0:
                # Signal exit
                trade_ret = pct_from_entry
                in_trade = False
                trade_returns.append(trade_ret)
                position_daily_returns.append(log_ret.iloc[i])
            else:
                position_daily_returns.append(log_ret.iloc[i])

    # ── Build equity curve ──────────────────────────────────────────────────
    pos_ret = pd.Series(position_daily_returns, index=close.index[: len(position_daily_returns)])
    equity_curve = (1 + pos_ret).cumprod()

    # ── Metrics ────────────────────────────────────────────────────────────
    total_return = float(equity_curve.iloc[-1] - 1)

    daily_ret = pos_ret.replace(0, np.nan).dropna()
    if len(daily_ret) > 1 and daily_ret.std() > 0:
        sharpe = float(daily_ret.mean() / daily_ret.std() * np.sqrt(252))
    else:
        sharpe = 0.0

    rolling_max = equity_curve.cummax()
    drawdowns = (equity_curve - rolling_max) / rolling_max
    max_drawdown = float(drawdowns.min())

    if trade_returns:
        wins = sum(1 for r in trade_returns if r > 0)
        win_rate = wins / len(trade_returns)
    else:
        win_rate = 0.0

    return BacktestResult(
        total_return=total_return,
        sharpe_ratio=sharpe,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        equity_curve=equity_curve,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Parameter sweep
# ──────────────────────────────────────────────────────────────────────────────

def sweep_parameter(
    prices: pd.DataFrame,
    param_name: str,
    param_values: List[float],
    base_params: Dict,
) -> pd.DataFrame:
    """
    Sweep one parameter across *param_values*, holding others at their base.

    Returns a DataFrame with columns:
        param_value, total_return, sharpe_ratio, max_drawdown, win_rate
    """
    records = []
    for val in param_values:
        p = {**base_params, param_name: val}
        try:
            r = run_sma_crossover(
                prices,
                fast_ma=int(p["fast_ma"]),
                slow_ma=int(p["slow_ma"]),
                stop_loss_pct=float(p["stop_loss_pct"]),
                take_profit_pct=float(p["take_profit_pct"]),
            )
            records.append(
                {
                    "param_value": val,
                    "total_return": r.total_return,
                    "sharpe_ratio": r.sharpe_ratio,
                    "max_drawdown": r.max_drawdown,
                    "win_rate": r.win_rate,
                }
            )
        except Exception:
            records.append(
                {
                    "param_value": val,
                    "total_return": np.nan,
                    "sharpe_ratio": np.nan,
                    "max_drawdown": np.nan,
                    "win_rate": np.nan,
                }
            )
    return pd.DataFrame(records)


# ──────────────────────────────────────────────────────────────────────────────
# Robustness scoring
# ──────────────────────────────────────────────────────────────────────────────

METRIC_COLS = ["total_return", "sharpe_ratio", "max_drawdown", "win_rate"]


def robustness_score_for_series(values: pd.Series) -> float:
    """
    Return a 0-100 robustness score based on coefficient of variation (CV).

    Low CV → high robustness.
    Score = 100 × exp(−k × CV),  k tuned so CV≈0.3 → score≈70.
    """
    clean = values.dropna()
    if len(clean) < 2:
        return 50.0
    mean = clean.mean()
    std = clean.std()
    if abs(mean) < 1e-9:
        cv = std
    else:
        cv = abs(std / mean)
    k = 3.5
    score = 100.0 * np.exp(-k * cv)
    return float(np.clip(score, 0, 100))


def compute_parameter_robustness(sweep_df: pd.DataFrame) -> Dict[str, float]:
    """Return per-metric robustness score for a single-parameter sweep DataFrame."""
    scores = {}
    for col in METRIC_COLS:
        if col in sweep_df.columns:
            scores[col] = robustness_score_for_series(sweep_df[col])
    return scores


def overall_robustness(per_param_scores: Dict[str, Dict[str, float]]) -> float:
    """Average of all per-parameter, per-metric scores."""
    all_scores = [
        s for param_scores in per_param_scores.values() for s in param_scores.values()
    ]
    if not all_scores:
        return 0.0
    return float(np.mean(all_scores))


def robustness_label(score: float) -> Tuple[str, str]:
    """Return (label, css-color-key) for a numeric score."""
    if score >= 70:
        return "Robust", "green"
    elif score >= 40:
        return "Moderate", "amber"
    else:
        return "Fragile", "red"


# ──────────────────────────────────────────────────────────────────────────────
# Heatmap data builder
# ──────────────────────────────────────────────────────────────────────────────

def build_heatmap_data(
    sweep_results: Dict[str, pd.DataFrame],
    base_params: Dict,
    base_metrics: Dict[str, float],
) -> pd.DataFrame:
    """
    Returns a DataFrame where rows = parameters, columns = metrics,
    values = % deviation of the *median sweep value* from the *base* metric.
    """
    rows = []
    for param_name, df in sweep_results.items():
        row = {"parameter": param_name}
        for metric in METRIC_COLS:
            if metric not in df.columns:
                row[metric] = np.nan
                continue
            base_val = base_metrics.get(metric, np.nan)
            if base_val is None or abs(base_val) < 1e-9:
                row[metric] = np.nan
            else:
                median_val = df[metric].median()
                row[metric] = abs((median_val - base_val) / base_val)
        rows.append(row)
    return pd.DataFrame(rows).set_index("parameter")