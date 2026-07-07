"""
hmm_utils.py
------------
A small, self-contained Gaussian Hidden Markov Model implementation used to
classify volatility regimes ("low-vol" vs "high-vol") for the Multi-Asset
Regime Backtester.

Why a hand-rolled HMM instead of a library?
  * Full control over the *forward algorithm* used for walk-forward
    inference, so we can guarantee the backtest never uses information
    from the future (no look-ahead bias).
  * Everything runs in the log domain with the standard log-sum-exp trick,
    so it stays numerically stable on long daily-return series.

Model
-----
A 1-D Gaussian HMM with `n_states` states (default 2). Each state k has a
mean and variance (diagonal/scalar covariance since we model a single
feature: the daily log return). States are estimated with Baum-Welch
(EM using forward-backward), then relabeled so that state 0 is always the
*lowest variance* ("low-vol") state and the last state is the
*highest variance* ("high-vol") state -- this fixes the classic HMM
label-switching problem and gives the rest of the app a stable convention.

Two ways to read state probabilities out of a fitted model:
  * `forward_filter`  -> causal / online filtering, P(state_t | obs_1..t).
                          This is what the backtest uses: it never peeks
                          at future observations.
  * `decode_viterbi`  -> full-sequence most-likely path (uses the whole
                          series). Handy for descriptive/diagnostic plots,
                          NOT used to generate trading signals.
"""

from __future__ import annotations

import numpy as np


_LOG_ZERO = -1e10  # stand-in for log(0) that stays finite for arithmetic


def _log_sum_exp(a: np.ndarray, axis: int = -1) -> np.ndarray:
    """Numerically stable log(sum(exp(a))) along an axis."""
    a_max = np.max(a, axis=axis, keepdims=True)
    a_max_safe = np.where(np.isfinite(a_max), a_max, 0.0)
    out = a_max_safe.squeeze(axis=axis) + np.log(
        np.sum(np.exp(a - a_max_safe), axis=axis) + 1e-300
    )
    return out


class GaussianHMM:
    """A minimal 1-D Gaussian Hidden Markov Model fit via Baum-Welch."""

    def __init__(
        self,
        n_states: int = 2,
        n_iter: int = 150,
        tol: float = 1e-4,
        random_state: int = 42,
        min_var: float = 1e-8,
    ):
        self.n_states = n_states
        self.n_iter = n_iter
        self.tol = tol
        self.random_state = random_state
        self.min_var = min_var

        # Fitted parameters (filled in by .fit)
        self.means_: np.ndarray | None = None
        self.vars_: np.ndarray | None = None
        self.transmat_: np.ndarray | None = None
        self.startprob_: np.ndarray | None = None
        self.converged_: bool = False
        self.n_iter_run_: int = 0
        self.log_likelihood_: float = -np.inf

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def _init_params(self, x: np.ndarray) -> None:
        rng = np.random.RandomState(self.random_state)
        n_states = self.n_states

        # Split observations into n_states quantile buckets to seed
        # means/vars. This is deterministic (given random_state) and
        # avoids needing an external clustering dependency.
        order = np.argsort(x)
        buckets = np.array_split(order, n_states)
        means = np.array([x[b].mean() for b in buckets])
        variances = np.array([max(x[b].var(), self.min_var) for b in buckets])

        # Sort by mean so initialization is reproducible/ordered; the
        # final post-fit relabeling (by variance) is what actually matters
        # for "low-vol" vs "high-vol" semantics.
        sort_idx = np.argsort(means)
        self.means_ = means[sort_idx]
        self.vars_ = variances[sort_idx]

        # Sticky transition matrix prior: regimes tend to persist.
        diag = 0.95
        off = (1 - diag) / max(n_states - 1, 1)
        self.transmat_ = np.full((n_states, n_states), off)
        np.fill_diagonal(self.transmat_, diag)

        self.startprob_ = np.full(n_states, 1.0 / n_states)

        # tiny random jitter on means so identical-looking states don't
        # stay perfectly tied during EM
        self.means_ = self.means_ + rng.normal(0, 1e-6, size=n_states)

    # ------------------------------------------------------------------
    # Emission probabilities
    # ------------------------------------------------------------------
    def _log_emission(self, x: np.ndarray) -> np.ndarray:
        """Return (T, n_states) log N(x_t; mean_k, var_k)."""
        x = x.reshape(-1, 1)
        var = np.maximum(self.vars_, self.min_var)
        log_prob = -0.5 * (
            np.log(2 * np.pi * var) + (x - self.means_) ** 2 / var
        )
        return log_prob

    # ------------------------------------------------------------------
    # Forward / backward (log domain)
    # ------------------------------------------------------------------
    def _forward_log(self, log_emission: np.ndarray):
        """Standard (causal) log-domain forward pass.

        Returns log_alpha of shape (T, n_states) where
        log_alpha[t, k] = log P(obs_1..t, state_t = k).
        Each row only depends on emissions up to and including t, so this
        is safe to use for online / walk-forward filtering.
        """
        T, n_states = log_emission.shape
        log_trans = np.log(np.maximum(self.transmat_, 1e-300))
        log_start = np.log(np.maximum(self.startprob_, 1e-300))

        log_alpha = np.zeros((T, n_states))
        log_alpha[0] = log_start + log_emission[0]
        for t in range(1, T):
            # log_alpha[t,k] = log_emission[t,k] + logsumexp_j(log_alpha[t-1,j] + log_trans[j,k])
            prev = log_alpha[t - 1][:, None] + log_trans  # (n_states_prev, n_states_next)
            log_alpha[t] = log_emission[t] + _log_sum_exp(prev, axis=0)
        return log_alpha

    def _backward_log(self, log_emission: np.ndarray):
        T, n_states = log_emission.shape
        log_trans = np.log(np.maximum(self.transmat_, 1e-300))

        log_beta = np.zeros((T, n_states))
        for t in range(T - 2, -1, -1):
            nxt = log_trans + (log_emission[t + 1] + log_beta[t + 1])[None, :]
            log_beta[t] = _log_sum_exp(nxt, axis=1)
        return log_beta

    # ------------------------------------------------------------------
    # Fit (Baum-Welch / EM)
    # ------------------------------------------------------------------
    def fit(self, x: np.ndarray) -> "GaussianHMM":
        x = np.asarray(x, dtype=float).reshape(-1)
        if len(x) < self.n_states * 5:
            raise ValueError("Not enough observations to fit the HMM.")

        self._init_params(x)
        prev_ll = -np.inf

        for iteration in range(self.n_iter):
            log_emission = self._log_emission(x)
            log_alpha = self._forward_log(log_emission)
            log_beta = self._backward_log(log_emission)

            ll = _log_sum_exp(log_alpha[-1], axis=0)

            # gamma[t,k] = P(state_t = k | all obs)
            log_gamma = log_alpha + log_beta
            log_gamma -= _log_sum_exp(log_gamma, axis=1)[:, None]
            gamma = np.exp(log_gamma)

            # xi[t,j,k] = P(state_t=j, state_{t+1}=k | all obs), summed over t
            log_trans = np.log(np.maximum(self.transmat_, 1e-300))
            T = len(x)
            xi_sum = np.zeros((self.n_states, self.n_states))
            for t in range(T - 1):
                log_xi_t = (
                    log_alpha[t][:, None]
                    + log_trans
                    + log_emission[t + 1][None, :]
                    + log_beta[t + 1][None, :]
                )
                log_xi_t -= _log_sum_exp(log_xi_t.reshape(-1))
                xi_sum += np.exp(log_xi_t)

            # M-step
            self.startprob_ = gamma[0] / gamma[0].sum()

            denom = xi_sum.sum(axis=1, keepdims=True)
            denom = np.where(denom < 1e-300, 1e-300, denom)
            self.transmat_ = xi_sum / denom

            gamma_sum = gamma.sum(axis=0)
            gamma_sum_safe = np.where(gamma_sum < 1e-300, 1e-300, gamma_sum)
            new_means = (gamma * x[:, None]).sum(axis=0) / gamma_sum_safe
            new_vars = (gamma * (x[:, None] - new_means) ** 2).sum(axis=0) / gamma_sum_safe
            self.means_ = new_means
            self.vars_ = np.maximum(new_vars, self.min_var)

            self.n_iter_run_ = iteration + 1
            if np.abs(ll - prev_ll) < self.tol:
                self.converged_ = True
                prev_ll = ll
                break
            prev_ll = ll

        self.log_likelihood_ = float(prev_ll)
        self._relabel_by_variance()
        return self

    def _relabel_by_variance(self) -> None:
        """Reorder states so state 0 = lowest variance ("low-vol") ...
        state n-1 = highest variance ("high-vol"). Fixes label-switching."""
        order = np.argsort(self.vars_)
        self.means_ = self.means_[order]
        self.vars_ = self.vars_[order]
        self.transmat_ = self.transmat_[order][:, order]
        self.startprob_ = self.startprob_[order]

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def forward_filter(self, x: np.ndarray) -> np.ndarray:
        """Causal filtered state probabilities, P(state_t | obs_1..t).

        Shape (T, n_states). Safe for walk-forward use: the value at row t
        is computed only from x[0..t], never from anything after t.
        """
        x = np.asarray(x, dtype=float).reshape(-1)
        log_emission = self._log_emission(x)
        log_alpha = self._forward_log(log_emission)
        log_norm = _log_sum_exp(log_alpha, axis=1)[:, None]
        filtered = np.exp(log_alpha - log_norm)
        return filtered

    def decode_viterbi(self, x: np.ndarray) -> np.ndarray:
        """Full-sequence most likely state path (uses the whole series --
        descriptive use only, not for generating causal trading signals)."""
        x = np.asarray(x, dtype=float).reshape(-1)
        log_emission = self._log_emission(x)
        T, n_states = log_emission.shape
        log_trans = np.log(np.maximum(self.transmat_, 1e-300))
        log_start = np.log(np.maximum(self.startprob_, 1e-300))

        delta = np.zeros((T, n_states))
        psi = np.zeros((T, n_states), dtype=int)
        delta[0] = log_start + log_emission[0]
        for t in range(1, T):
            scores = delta[t - 1][:, None] + log_trans
            psi[t] = np.argmax(scores, axis=0)
            delta[t] = np.max(scores, axis=0) + log_emission[t]

        path = np.zeros(T, dtype=int)
        path[-1] = np.argmax(delta[-1])
        for t in range(T - 2, -1, -1):
            path[t] = psi[t + 1, path[t + 1]]
        return path


def fit_and_label_regimes(
    train_returns: np.ndarray,
    test_returns: np.ndarray,
    n_states: int = 2,
    random_state: int = 42,
):
    """Fit a GaussianHMM on `train_returns` only, then run the *forward
    algorithm only* (causal filtering) across train+test to label the
    test segment's regimes without any look-ahead.

    Returns
    -------
    dict with:
      'model'            : fitted GaussianHMM
      'test_regime'      : (len(test_returns),) int array, argmax filtered
                            state for each test-period day
      'test_posterior'   : (len(test_returns), n_states) filtered probs
      'train_regime'     : argmax filtered state for the train period
                            (diagnostic / display only)
    """
    train_returns = np.asarray(train_returns, dtype=float).reshape(-1)
    test_returns = np.asarray(test_returns, dtype=float).reshape(-1)

    model = GaussianHMM(n_states=n_states, random_state=random_state)
    model.fit(train_returns)

    combined = np.concatenate([train_returns, test_returns])
    filtered = model.forward_filter(combined)  # causal at every t

    n_train = len(train_returns)
    train_posterior = filtered[:n_train]
    test_posterior = filtered[n_train:]

    return {
        "model": model,
        "test_regime": np.argmax(test_posterior, axis=1),
        "test_posterior": test_posterior,
        "train_regime": np.argmax(train_posterior, axis=1),
        "train_posterior": train_posterior,
    }