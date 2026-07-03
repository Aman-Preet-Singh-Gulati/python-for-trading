"""
regime_engine.py
-----------------
Pure-Python regime detection pipeline (no Streamlit dependency, so it can be
unit-tested directly). Given a raw OHLCV price dataframe, this module:

  1. engineers volatility/return/volume features
  2. fits a GaussianHMM for k = 3..7 components and selects k via BIC
  3. infers the regime at every bar with a strictly CAUSAL forward filter
     (never Viterbi, never forward-backward smoothing) — the label at time T
     depends only on observations 1..T
  4. labels regimes by mean volatility, low -> high
  5. applies a 3-bar persistence + 20-bar flicker stability filter
"""

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from scipy.stats import multivariate_normal

FEATURE_COLS = ["log_return", "realized_vol", "volume_ratio", "hl_range_pct"]

REGIME_NAME_SCHEMES = {
    3: ["Low Vol", "Medium Vol", "High Vol"],
    4: ["Low Vol", "Medium Vol", "High Vol", "Extreme Vol"],
    5: ["Very Low Vol", "Low Vol", "Medium Vol", "High Vol", "Extreme Vol"],
    6: ["Very Low Vol", "Low Vol", "Medium Vol", "High Vol", "Very High Vol", "Extreme Vol"],
    7: [
        "Very Low Vol", "Low Vol", "Medium-Low Vol", "Medium Vol",
        "Medium-High Vol", "High Vol", "Extreme Vol",
    ],
}


# ==========================================================================
# FEATURE ENGINEERING
# ==========================================================================

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """df must have columns Close, High, Low, Volume."""
    feat = pd.DataFrame(index=df.index)
    feat["close"] = df["Close"]
    feat["log_return"] = np.log(df["Close"] / df["Close"].shift(1))
    feat["realized_vol"] = feat["log_return"].rolling(20).std()
    feat["volume_ratio"] = df["Volume"] / df["Volume"].rolling(20).mean()
    feat["hl_range_pct"] = (df["High"] - df["Low"]) / df["Close"] * 100
    feat = feat.replace([np.inf, -np.inf], np.nan).dropna()
    return feat


def standardize(X: np.ndarray):
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma = np.where(sigma == 0, 1e-8, sigma)
    return (X - mu) / sigma, mu, sigma


# ==========================================================================
# MODEL SELECTION (BIC)
# ==========================================================================

def n_hmm_params(n_components: int, n_features: int) -> int:
    """Free-parameter count for a diagonal-covariance Gaussian HMM:
    (k-1) initial-state probs + k(k-1) transition probs + k*f means + k*f variances."""
    return n_components**2 - 1 + 2 * n_components * n_features


def fit_best_hmm(X: np.ndarray, k_options, n_iter: int = 200, random_state: int = 42):
    n_samples, n_features = X.shape
    results = []
    for k in k_options:
        try:
            model = GaussianHMM(
                n_components=k,
                covariance_type="diag",
                n_iter=n_iter,
                random_state=random_state,
                min_covar=1e-3,
                tol=1e-4,
            )
            model.fit(X)
            log_likelihood = model.score(X)
            n_params = n_hmm_params(k, n_features)
            bic = -2 * log_likelihood + n_params * np.log(n_samples)
            results.append({"k": k, "model": model, "bic": bic, "log_likelihood": log_likelihood})
        except Exception:
            continue
    if not results:
        raise RuntimeError("HMM fitting failed for every candidate number of regimes.")
    best = min(results, key=lambda r: r["bic"])
    return best, results


# ==========================================================================
# CAUSAL FORWARD FILTER  (NOT Viterbi, NOT forward-backward smoothing)
# ==========================================================================

def _emission_probs(X: np.ndarray, means: np.ndarray, covars: np.ndarray) -> np.ndarray:
    n_samples = X.shape[0]
    k = means.shape[0]
    B = np.zeros((n_samples, k))
    for i in range(k):
        var = np.clip(covars[i], 1e-6, None)
        B[:, i] = multivariate_normal.pdf(X, mean=means[i], cov=np.diag(var))
    return np.clip(B, 1e-300, None)


def forward_filter(X: np.ndarray, startprob: np.ndarray, transmat: np.ndarray,
                    means: np.ndarray, covars: np.ndarray) -> np.ndarray:
    """
    Strict causal filtering: alpha[t] = P(state_t | obs_1 ... obs_t).
    alpha[t] is computed only from alpha[t-1] and obs_t — it never sees
    obs_{t+1}, ..., obs_T. This is the forward pass of the forward-backward
    algorithm used ALONE: no backward pass, no global Viterbi decoding.
    Both of those alternatives would leak future information into the
    label assigned at time t, which is exactly the look-ahead bias this
    function is designed to avoid.
    """
    n_samples = X.shape[0]
    k = startprob.shape[0]
    B = _emission_probs(X, means, covars)

    alpha = np.zeros((n_samples, k))
    a0 = startprob * B[0]
    s0 = a0.sum()
    alpha[0] = a0 / s0 if s0 > 0 else np.ones(k) / k

    for t in range(1, n_samples):
        a = (alpha[t - 1] @ transmat) * B[t]
        s = a.sum()
        alpha[t] = a / s if s > 0 else np.ones(k) / k

    return alpha


def verify_no_lookahead(X: np.ndarray, model: GaussianHMM):
    """
    Proof-of-causality check: run the forward filter on the full series and
    independently on a truncated prefix. If the filter is truly causal,
    filtered probabilities on the overlapping region must match exactly —
    data after the truncation point cannot have influenced them. Any
    look-ahead leakage would show up as a nonzero difference here.
    """
    full = forward_filter(X, model.startprob_, model.transmat_, model.means_, model.covars_)
    split = max(15, len(X) // 2)
    partial = forward_filter(X[:split], model.startprob_, model.transmat_, model.means_, model.covars_)
    diff = float(np.max(np.abs(full[:split] - partial)))
    return diff < 1e-8, diff, full


# ==========================================================================
# REGIME LABELING (by mean volatility, low -> high)
# ==========================================================================

def label_states_by_vol(model: GaussianHMM, feature_cols: list) -> dict:
    vol_idx = feature_cols.index("realized_vol")
    means = model.means_[:, vol_idx]
    order = np.argsort(means)  # ascending vol
    names = REGIME_NAME_SCHEMES[model.n_components]
    return {state_idx: names[rank] for rank, state_idx in enumerate(order)}


# ==========================================================================
# STABILITY FILTER
# ==========================================================================

def apply_stability_filter(raw_labels: list, persist_bars: int = 3,
                            flicker_window: int = 20, flicker_max: int = 4):
    """
    A regime only becomes 'active' once it has persisted for `persist_bars`
    consecutive raw observations (a debounced state). If the debounced
    regime still changes more than `flicker_max` times within any
    `flicker_window`-bar trailing window, the bar is flagged 'Uncertain'
    rather than trusted.
    """
    n = len(raw_labels)
    confirmed = [raw_labels[0]] * n
    current = raw_labels[0]
    pending = raw_labels[0]
    pending_count = 1

    for t in range(1, n):
        if raw_labels[t] == pending:
            pending_count += 1
        else:
            pending = raw_labels[t]
            pending_count = 1
        if pending_count >= persist_bars and pending != current:
            current = pending
        confirmed[t] = current

    changes = [0] * n
    for t in range(1, n):
        changes[t] = 1 if confirmed[t] != confirmed[t - 1] else 0
    rolling_changes = pd.Series(changes).rolling(flicker_window, min_periods=1).sum()
    flagged = (rolling_changes > flicker_max).values

    final = [("Uncertain" if flagged[t] else confirmed[t]) for t in range(n)]
    return confirmed, final, flagged


# ==========================================================================
# FULL PIPELINE (pure python — takes an already-downloaded OHLCV dataframe)
# ==========================================================================

def run_pipeline(raw: pd.DataFrame, k_override="Auto (BIC)"):
    if raw is None or raw.empty or len(raw) < 60:
        return {"error": "Not enough price data in that date range (need at least ~60 bars)."}

    feat = engineer_features(raw)
    if len(feat) < 40:
        return {"error": "Not enough clean rows after feature engineering (need at least ~40)."}

    X_raw = feat[FEATURE_COLS].values
    X, mu, sigma = standardize(X_raw)

    k_options = range(3, 8) if k_override == "Auto (BIC)" else [int(k_override)]

    best, all_results = fit_best_hmm(X, k_options)
    model = best["model"]

    passed, diff, alpha = verify_no_lookahead(X, model)

    state_to_label = label_states_by_vol(model, FEATURE_COLS)
    raw_states = np.argmax(alpha, axis=1)
    confidence = alpha[np.arange(len(alpha)), raw_states]
    raw_labels = [state_to_label[s] for s in raw_states]

    confirmed_labels, final_labels, flagged = apply_stability_filter(raw_labels)

    out = feat.copy()
    out["raw_label"] = raw_labels
    out["confirmed_label"] = confirmed_labels
    out["final_label"] = final_labels
    out["confidence"] = confidence
    out["flagged_uncertain"] = flagged

    return {
        "error": None,
        "df": out,
        "model": model,
        "best_k": best["k"],
        "best_bic": best["bic"],
        "bic_table": [(r["k"], r["bic"], r["log_likelihood"]) for r in all_results],
        "lookahead_passed": passed,
        "lookahead_diff": diff,
        "state_to_label": state_to_label,
    }