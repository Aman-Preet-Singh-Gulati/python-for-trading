"""
Utilities for the Monte Carlo dashboard — plain-English guide for non-traders.

This module contains helpers used by the dashboard. Each function below has
an immediately preceding comment that explains, in simple terms, what it
does, how it does it, and a tiny numeric example so a reader with no trading
knowledge can follow along.

Basic trading terms used here:
- trade return: single-trade profit/loss expressed as a fraction (0.01 = +1%).
- equity curve: running account balance after each trade (start, after trade1, ...).
- drawdown: how far the account falls from a previous peak ((peak - value)/peak).

Why these functions exist:
- Generate demo trade returns when you don't have real data.
- Convert lists of returns into equity curves and risk metrics.
- Run Monte Carlo simulations by shuffling trade order and adding small noise
    to estimate the range of possible outcomes.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Optional


def generate_demo_data(n_trades: int = 200, seed: int = 42) -> pd.DataFrame:
    """
    Purpose:
    - Create a synthetic list of trades (dates + trade returns) for demos.

    How it works (simple):
    1) Use a random seed so results are repeatable.
    2) For each trade, randomly mark it as a "win" (55% chance) or "loss".
    3) Wins get a random positive return around +1.2%; losses around -0.8%.
    4) Returns are clamped to a realistic band to avoid extreme outliers.

    Tiny example:
    - If n_trades=3, possible trade_return values might be [0.015, -0.006, 0.010]
    - Returned DataFrame columns: date (datetime), trade_return (float)
    """
    rng = np.random.default_rng(seed)

    # Win rate ~55%, average win > average loss (slight edge)
    win_mask = rng.random(n_trades) < 0.55

    returns = np.where(
        win_mask,
        rng.normal(0.012, 0.018, n_trades),   # wins: avg +1.2%
        rng.normal(-0.008, 0.012, n_trades),   # losses: avg -0.8%
    )

    # Clamp to realistic range
    returns = np.clip(returns, -0.12, 0.18)

    dates = pd.date_range(start="2021-01-01", periods=n_trades, freq="B")
    return pd.DataFrame({"date": dates, "trade_return": returns})


def compute_equity_curve(returns: np.ndarray, starting_capital: float) -> np.ndarray:
    """
    Purpose:
    - Convert a sequence of trade returns into an account balance over time.

    How it works (simple):
    - equity[0] = starting capital
    - after each trade: equity *= (1 + trade_return)

    Tiny example:
    - returns = [0.10, -0.05], starting_capital = 100
    - equity -> [100.0, 110.0, 104.5]
    """
    equity = np.empty(len(returns) + 1)
    equity[0] = starting_capital
    np.cumprod(1.0 + returns, out=equity[1:])
    equity[1:] *= starting_capital
    return equity


def compute_max_drawdown(equity: np.ndarray) -> float:
    """
    Purpose:
    - Find the largest percent drop from a prior peak in the equity series.

    How it works (simple):
    - For each point compute running peak, then (peak - value)/peak.
    - Return the maximum of those values.

    Tiny example:
    - equity = [100, 120, 90, 130] -> drawdowns = [0,0,0.25,0] -> return 0.25
    """
    peak = np.maximum.accumulate(equity)
    drawdown = (peak - equity) / peak
    return float(drawdown.max())


def run_monte_carlo(
    returns: np.ndarray,
    starting_capital: float,
    n_simulations: int,
    noise_pct: float = 0.003,
    seed: int = 0,
) -> Dict:
    """
    Purpose:
    - Create many alternate "realities" by re-ordering (shuffling) the same
      set of trade returns and adding a tiny random perturbation to each trade.

    How it works (simple):
    1) Repeat n_simulations times:
       - shuffle the input returns (change order)
       - add small uniform noise in [-noise_pct, +noise_pct] to each trade
       - compute the equity curve and max drawdown for that simulation
    2) Collect final values and drawdowns across all simulations
    3) Compute stats: median, percentiles (5/25/75/95), probability of loss,
       probability of drawdowns > 20%/30%, and where the original backtest
       ranks among the simulated outcomes (original_pct_rank).

    Returns a dict with:
        equity_curves  – (n_simulations, n_trades+1) array
        max_drawdowns  – (n_simulations,) array
        final_values   – (n_simulations,) array
        original_equity – (n_trades+1,) array
        original_dd    – float
        stats          – summary statistics dict

    Tiny conceptual example (toy):
    - returns = [0.01, -0.02, 0.03], starting_capital = 1000
    - shuffle and compute final for a few sims -> final values may be [1030,1060,1010]
    - median_final ~ 1030, prob_loss = fraction < 1000
    """
    rng = np.random.default_rng(seed)
    n = len(returns)

    equity_curves = np.empty((n_simulations, n + 1))
    max_drawdowns = np.empty(n_simulations)

    for i in range(n_simulations):
        shuffled = rng.permutation(returns)
        noise = rng.uniform(-noise_pct, noise_pct, n)
        sim_returns = shuffled + noise
        eq = compute_equity_curve(sim_returns, starting_capital)
        equity_curves[i] = eq
        max_drawdowns[i] = compute_max_drawdown(eq)

    final_values = equity_curves[:, -1]
    original_equity = compute_equity_curve(returns, starting_capital)
    original_dd = compute_max_drawdown(original_equity)

    original_final = original_equity[-1]
    pct_rank = float(np.mean(final_values < original_final))

    stats = {
        "median_final": float(np.median(final_values)),
        "p5_final": float(np.percentile(final_values, 5)),
        "p25_final": float(np.percentile(final_values, 25)),
        "p75_final": float(np.percentile(final_values, 75)),
        "p95_final": float(np.percentile(final_values, 95)),
        "prob_loss": float(np.mean(final_values < starting_capital)),
        "prob_dd_20": float(np.mean(max_drawdowns > 0.20)),
        "prob_dd_30": float(np.mean(max_drawdowns > 0.30)),
        "median_max_dd": float(np.median(max_drawdowns)),
        "p95_max_dd": float(np.percentile(max_drawdowns, 95)),
        "original_final": float(original_final),
        "original_dd": original_dd,
        "original_pct_rank": pct_rank,
        "overfitting_flag": pct_rank > 0.90,
        "starting_capital": starting_capital,
        "n_simulations": n_simulations,
        "n_trades": n,
    }

    return {
        "equity_curves": equity_curves,
        "max_drawdowns": max_drawdowns,
        "final_values": final_values,
        "original_equity": original_equity,
        "original_dd": original_dd,
        "stats": stats,
    }


def validate_csv(df: pd.DataFrame) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
        Purpose:
        - Ensure an uploaded CSV contains the expected columns, types and enough
            rows to be useful for simulation.

        How it works (simple):
        - Normalize column names to lowercase, require 'date' and 'trade_return'.
        - Parse 'date' into datetimes, coerce 'trade_return' to numeric.
        - Require at least 10 rows; sort by date and return the cleaned DataFrame.

        Tiny example:
        - Input columns: Date, Trade_Return (strings/numbers)
        - Output: DataFrame with 'date' (datetime) and 'trade_return' (float), sorted
    """
    required = {"date", "trade_return"}
    cols = {c.strip().lower() for c in df.columns}
    missing = required - cols

    if missing:
        return False, f"Missing columns: {', '.join(missing)}. Need 'date' and 'trade_return'.", None

    # Normalise column names
    df = df.rename(columns={c: c.strip().lower() for c in df.columns})

    try:
        df["date"] = pd.to_datetime(df["date"])
    except Exception:
        return False, "Could not parse 'date' column as dates.", None

    try:
        df["trade_return"] = pd.to_numeric(df["trade_return"], errors="raise")
    except Exception:
        return False, "'trade_return' column must be numeric.", None

    if len(df) < 10:
        return False, f"Need at least 10 trades, got {len(df)}.", None

    df = df.sort_values("date").reset_index(drop=True)
    return True, f"Loaded {len(df)} trades.", df


def format_currency(value: float) -> str:
    """Format a number as dollar currency for display (rounded, with commas).

    Example: 123456.7 -> "$123,457"
    """
    return f"${value:,.0f}"


def format_pct(value: float, decimals: int = 1) -> str:
    """Format a fractional value as a percentage string.

    Example: 0.1234 -> "12.3%"
    """
    return f"{value * 100:.{decimals}f}%"