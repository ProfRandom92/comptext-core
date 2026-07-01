"""
pcomptext/core/statistical_engine.py

Probabilistic analysis core.
- Token entropy from real logprobs (Shannon entropy)
- Diff-style comparison using difflib
- Ported Bayesian/MCMC comparative text analysis math from comptext_v2/agents/logic.js
"""

from __future__ import annotations
import difflib
from functools import lru_cache
import math
import re
from typing import Any, Dict, List, Tuple
import threading
import blake3

import numpy as np

# --- Existing Statistical Engine Functions ---

def token_entropy_from_logprobs(token_logprob: dict[str, Any]) -> float:
    """Compute Shannon entropy for one token using its top_logprobs. Public for CLI heatmap."""
    top = token_logprob.get("top_logprobs", [])
    if not top:
        # Fallback using the returned logprob
        p = math.exp(token_logprob.get("logprob", -10.0))
        return -p * math.log2(max(p, 1e-12))
    probs = [math.exp(item["logprob"]) for item in top]
    s = sum(probs)
    if s <= 0:
        return 0.0
    probs = [p / s for p in probs]
    ent = -sum(p * math.log2(max(p, 1e-12)) for p in probs)
    return float(ent)

def compute_sequence_entropy(logprobs: list[dict[str, Any]]) -> dict[str, float]:
    """
    Aggregate entropy stats for a full generation.
    Expects list of {"token": str, "logprob": float, "top_logprobs": [...]}
    """
    if not logprobs:
        return {"mean": 0.0, "std": 0.0, "total": 0.0, "count": 0}

    token_ents = [token_entropy_from_logprobs(lp) for lp in logprobs]
    return {
        "mean": float(np.mean(token_ents)),
        "std": float(np.std(token_ents)),
        "total": float(np.sum(token_ents)),
        "count": len(token_ents),
    }

def compute_diff_style_comparison(text1: str, text2: str, label1: str = "sample_0", label2: str = "sample_1") -> str:
    """Aider-style unified diff for variance visualization."""
    a = text1.splitlines(keepends=True)
    b = text2.splitlines(keepends=True)
    diff = difflib.unified_diff(a, b, fromfile=label1, tofile=label2, lineterm="")
    return "".join(diff)

def recommend_sampling_params(past_entropies: list[float]) -> dict[str, float]:
    """Simple cuOpt-inspired heuristic for temperature/top_p tuning."""
    if not past_entropies:
        return {"temperature": 0.7, "top_p": 0.95}

    avg = float(np.mean(past_entropies))
    if avg > 1.5:
        # High uncertainty -> more deterministic
        return {"temperature": max(0.1, 0.4 - (avg - 1.5) * 0.2), "top_p": 0.85}
    if avg < 0.3:
        # Low uncertainty -> more creative
        return {"temperature": min(1.0, 0.6 + (0.3 - avg) * 1.5), "top_p": 0.95}
    return {"temperature": 0.7, "top_p": 0.95}


# --- Ported Bayesian, Bootstrap, and MCMC Mathematics from comptext_v2 ---

# Seeded PRNG state (mulberry32 implementation in Python)
_seed = 0x12345678

def set_seed(s: int) -> None:
    """Set PRNG seed for reproducible results."""
    global _seed
    _seed = (int(s) & 0xFFFFFFFF) or 0x12345678

def get_current_seed() -> int:
    """Get the current PRNG seed."""
    return _seed & 0xFFFFFFFF

def seeded_random() -> float:
    """Simple seeded PRNG (mulberry32) for reproducible statistical calculations."""
    global _seed
    _seed = (_seed + 0x6D2B79F5) & 0xFFFFFFFF
    t = _seed
    
    t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
    t = (t + ((t ^ (t >> 7)) * (t | 61))) & 0xFFFFFFFF
    
    return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

def reset(new_seed: int | None = None) -> None:
    """Reset RNG to default seed or a custom seed."""
    if isinstance(new_seed, int):
        set_seed(new_seed)
    else:
        global _seed
        _seed = 0x12345678

class ThreadSafeSentimentLexicon:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        with self._lock:
            if getattr(self, "_initialized", False):
                return
            self.vocab = [
                'excellent', 'great', 'love', 'positive', 'reliable', 'fast', 'quality', 'innovation', 'success', 'adaptive',
                'mediocre', 'poor', 'negative', 'slow', 'defect', 'disappointment', 'break', 'static', 'conservative', 'robust'
            ]
            self.vocab_set = set(self.vocab)
            self._initialized = True

    def expand(self, new_terms: list[str]) -> list[str]:
        added = []
        with self._lock:
            for term in new_terms:
                term_clean = term.lower().strip()
                if term_clean and term_clean not in self.vocab_set:
                    self.vocab.append(term_clean)
                    self.vocab_set.add(term_clean)
                    added.append(term_clean)
        return added

    def get_vocab(self) -> list[str]:
        with self._lock:
            return list(self.vocab)

    def contains(self, token: str) -> bool:
        if not token:
            return False
        with self._lock:
            return token.lower() in self.vocab_set

# Singleton instance
_lexicon = ThreadSafeSentimentLexicon()
SENTIMENT_VOCAB = _lexicon.vocab
_sentiment_set = _lexicon.vocab_set

def expand_sentiment_lexicon(new_terms: list[str]) -> list[str]:
    """Dynamically expand sentiment vocabulary (e.g. from lexicon discovery) thread-safely."""
    return _lexicon.expand(new_terms)

def get_sentiment_vocab() -> list[str]:
    """Return a copy of the sentiment vocabulary thread-safely."""
    return _lexicon.get_vocab()

def is_sentiment_term(token: str) -> bool:
    """Check if token is in sentiment vocabulary thread-safely."""
    return _lexicon.contains(token)

@lru_cache(maxsize=1024)
def _tokenize_cached(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    cleaned = re.sub(r'[^a-zäöüß\s]', ' ', lowered)
    return tuple(w for w in cleaned.split() if w)

def tokenize(text: str) -> list[str]:
    """Tokenize raw text into normalized lowercase word tokens."""
    if not text or not isinstance(text, str):
        return []
    return list(_tokenize_cached(text))

def tokens_to_theta(tokens: list[str], dim: int = 8, prior_strength: float = 1e-4) -> list[float]:
    """
    Create a fixed-dimensional feature vector (latent proxy) from tokens.
    Uses hashing + frequency for reproducibility, regularized by a Dirichlet-like prior.
    """
    vec = [0.0] * dim
    if not tokens:
        u = prior_strength / dim
        s = u * dim or 1.0
        return [u / s] * dim

    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1

    for word, count in freq.items():
        h = 0
        for char in word:
            h = (h * 31 + ord(char)) & 0xFFFFFFFF
        idx = h % dim
        vec[idx] += count

    total_sum = 0.0
    for i in range(dim):
        vec[i] += prior_strength
        total_sum += vec[i]

    denom = total_sum or 1.0
    return [v / denom for v in vec]

def tokens_to_counts(tokens: list[str], dim: int) -> list[int]:
    """Helper to compute raw counts per dim bin from tokens without prior or normalization."""
    vec = [0] * dim
    if not tokens:
        return vec
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    for word, count in freq.items():
        h = 0
        for char in word:
            h = (h * 31 + ord(char)) & 0xFFFFFFFF
        idx = h % dim
        vec[idx] += count
    return vec

def bootstrap_thetas(text: str, B: int, dim: int = 8, noise_sigma: float = 0.0) -> list[list[float]]:
    """
    Sample bootstrap replicates of theta vectors.
    Precomputes sentence-frequency vectors and aggregates them in a vectorized manner
    to avoid redundant string tokenization and hashing operations inside the loop.
    """
    tokens = tokenize(text)
    if not tokens:
        return [tokens_to_theta([], dim) for _ in range(B)]

    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    observations = sentences if len(sentences) > 1 else [text]
    n_obs = len(observations)

    # Precompute raw frequency counts for each observation sentence
    obs_tokens = [tokenize(obs) for obs in observations]
    obs_counts = [tokens_to_counts(toks, dim) for toks in obs_tokens]
    
    # Cast to a numpy array for fast addition
    obs_matrix = np.array(obs_counts, dtype=np.float64)

    replicates = []
    prior_strength = 1e-4
    for _ in range(B):
        # We must draw pick_idx using seeded_random() to preserve reproducibility
        sum_vec = np.zeros(dim, dtype=np.float64)
        for _ in range(n_obs):
            pick_idx = int(seeded_random() * n_obs)
            sum_vec += obs_matrix[pick_idx]
            
        # Add prior_strength and L1-normalize
        sum_vec += prior_strength
        denom = np.sum(sum_vec) or 1.0
        theta = sum_vec / denom
        
        if noise_sigma > 0.0:
            noisy_theta = []
            for v in theta:
                u = max(1e-9, seeded_random())
                v2 = seeded_random()
                z = math.sqrt(-2.0 * math.log(u)) * math.cos(2.0 * math.pi * v2)
                noisy = v + z * noise_sigma
                noisy_theta.append(max(0.0, noisy))
            
            denom_noise = sum(noisy_theta) or 1.0
            theta_res = [v / denom_noise for v in noisy_theta]
        else:
            theta_res = theta.tolist()

        replicates.append(theta_res)
    return replicates

def compute_bootstrap_variance(thetas: list[list[float]]) -> list[float]:
    """Compute unbiased sample variance per dimension across bootstrap replicates."""
    if not thetas:
        return []
    arr = np.array(thetas, dtype=np.float64)
    if len(arr) < 2:
        return [0.0] * arr.shape[1]
    return np.var(arr, axis=0, ddof=1).tolist()

def compute_credible_intervals(thetas: list[list[float]], qs: list[float] | None = None) -> dict[str, Any]:
    """
    Compute quantile-based credible intervals (ETI) and basic stats
    (mean, standard deviation, effective sample size) per dimension.
    """
    if qs is None:
        qs = [0.025, 0.5, 0.975]
    if not thetas:
        return {}
    
    arr = np.array(thetas, dtype=np.float64)
    B, d = arr.shape
    
    means = np.mean(arr, axis=0)
    sds = np.std(arr, axis=0, ddof=1) if B > 1 else np.zeros(d)
    
    ess = [round(compute_effective_sample_size(arr[:, i].tolist()), 1) for i in range(d)]
    
    sorted_arr = np.sort(arr, axis=0)
    intervals = []
    for q in qs:
        idx = int((B - 1) * q)
        idx_clamped = max(0, min(B - 1, idx))
        intervals.append({
            "q": q,
            "values": [round(float(val), 8) for val in sorted_arr[idx_clamped]]
        })
        
    return {
        "intervals": intervals,
        "means": [round(float(val), 8) for val in means],
        "sds": [round(float(val), 8) for val in sds],
        "ess": ess,
        "n": B
    }

def compute_hdi_credible(thetas: list[list[float]], prob: float = 0.89) -> dict[str, Any]:
    """Approximate Highest Density Interval (HDI) containing specified probability mass per dimension."""
    if not thetas:
        return {"prob": prob, "hdi": []}
    arr = np.array(thetas, dtype=np.float64)
    B, d = arr.shape
    
    sorted_arr = np.sort(arr, axis=0)
    window = max(1, int(B * prob))
    
    hdis = []
    for col in range(d):
        samples = sorted_arr[:, col]
        i_indices = np.arange(B - window + 1)
        widths = samples[i_indices + window - 1] - samples[i_indices]
        best_idx = np.argmin(widths)
        hdis.append([
            round(float(samples[best_idx]), 8),
            round(float(samples[best_idx + window - 1]), 8)
        ])
    return {"prob": prob, "hdi": hdis}

def compute_effective_sample_size(chain: list[float]) -> float:
    """Compute effective sample size (ESS) using a simple AR(1) autocorrelation approximation."""
    if not chain:
        return 0.0
    arr = np.array(chain, dtype=np.float64)
    n = len(arr)
    if n < 4:
        return float(n)
        
    mean = np.mean(arr)
    centered = arr - mean
    c0 = np.sum(centered ** 2) / n
    if c0 <= 0.0:
        return float(n)
        
    c1 = np.sum(centered[1:] * centered[:-1]) / n
    
    rho = max(-0.99, min(0.99, c1 / c0))
    ess = n * (1.0 - rho) / (1.0 + rho)
    if not math.isfinite(ess) or ess <= 0.0:
        ess = n
    return min(float(n), max(1.0, ess))

def compute_sentiment_distribution(text: str, alpha: float = 0.5) -> dict[str, float]:
    """Compute smoothed empirical probability distribution over the sentiment lexicon."""
    tokens = tokenize(text)
    counts = {}
    total = 0
    for w in tokens:
        if is_sentiment_term(w):
            counts[w] = counts.get(w, 0) + 1
            total += 1

    dist = {}
    vocab = get_sentiment_vocab()
    V = len(vocab)
    denom = (total + alpha * V) or 1.0

    for w in vocab:
        c = counts.get(w, 0)
        dist[w] = (c + alpha) / denom
    return dist

def kl_divergence(p1: dict[str, float], p2: dict[str, float]) -> float:
    """Calculate Shannon Kullback-Leibler Divergence between two probability distributions."""
    vocab = get_sentiment_vocab()
    v1 = np.array([p1.get(w, 0.0) for w in vocab])
    v2 = np.array([p2.get(w, 1e-12) or 1e-12 for w in vocab])
    
    mask = v1 > 0.0
    if not np.any(mask):
        return 0.0
    return float(max(0.0, np.sum(v1[mask] * np.log(v1[mask] / v2[mask]))))

def approximate_tangent_direction(theta_a: list[float], theta_b: list[float]) -> list[float]:
    """Approximate the units tangent vector direction from difference of mean representation vectors."""
    a = np.array(theta_a, dtype=np.float64)
    b = np.array(theta_b, dtype=np.float64)
    diff = b - a
    norm = np.linalg.norm(diff) or 1.0
    return (diff / norm).tolist()

def compute_dpc_gap(thetas: list[list[float]], theta_mean: list[float], tangent: list[float]) -> dict[str, Any]:
    """
    Compute Dynamic Probabilistic Consistency (DPC) Gap.
    Measures the alignment between the units variance direction and unit tangent vector.
    """
    if not thetas or not tangent:
        return {"gap": 1.0, "cosine": 0.0, "varianceDirection": []}

    variances = compute_bootstrap_variance(thetas)
    vdir = np.sqrt(np.maximum(0.0, variances))
    norm = np.linalg.norm(vdir) or 1.0
    vdir = vdir / norm

    t_arr = np.array(tangent, dtype=np.float64)
    if len(t_arr) < len(vdir):
        pad_t = np.zeros_like(vdir)
        pad_t[:len(t_arr)] = t_arr
        t_arr = pad_t
    elif len(t_arr) > len(vdir):
        t_arr = t_arr[:len(vdir)]

    dot = np.dot(vdir, t_arr)
    cosine = max(-1.0, min(1.0, dot))
    gap = abs(cosine)

    return {
        "gap": round(float(gap), 6),
        "cosine": round(float(cosine), 6),
        "varianceDirection": [round(float(x), 5) for x in vdir]
    }

def compute_dpc_gap_with_uncertainty(thetas: list[list[float]], theta_mean: list[float], tangent: list[float], n_sub: int = 30) -> dict[str, Any]:
    """Compute DPC Gap with 5%-95% uncertainty confidence bands via bootstrapping of bootstraps."""
    base = compute_dpc_gap(thetas, theta_mean, tangent)
    if not thetas or len(thetas) < 5:
        return {**base, "gapCI": [base["gap"], base["gap"]]}

    gaps = []
    n = len(thetas)
    for _ in range(n_sub):
        sub = []
        used = set()
        sub_limit = min(20, int(n * 0.7))
        while len(sub) < sub_limit:
            idx = int(seeded_random() * n)
            if idx not in used:
                used.add(idx)
                sub.append(thetas[idx])
        g = compute_dpc_gap(sub, theta_mean, tangent)
        gaps.append(g["gap"])

    gaps.sort()
    lo = gaps[int(len(gaps) * 0.05)] if gaps else base["gap"]
    hi = gaps[int(len(gaps) * 0.95)] if gaps else base["gap"]
    return {
        **base,
        "gapCI": [round(min(lo, hi), 6), round(max(lo, hi), 6)]
    }

def decompose_variance(thetas: list[list[float]]) -> dict[str, Any]:
    """Decompose bootstrap variance into trace sum, mean variance, and components."""
    if not thetas:
        return {"totalTrace": 0.0, "perDim": [], "meanVar": 0.0, "n": 0}
    vars_list = compute_bootstrap_variance(thetas)
    total_trace = sum(vars_list)
    mean_var = total_trace / max(1, len(vars_list))
    return {
        "totalTrace": round(total_trace, 10),
        "perDim": [round(v, 8) for v in vars_list],
        "meanVar": round(mean_var, 8),
        "n": len(thetas)
    }

def simulate_posterior_predictive(thetas: list[list[float]], n_pred: int = 20) -> dict[str, Any]:
    """Simulate posterior predictive replicates with L2 discrepancy checks (PPC diagnostics)."""
    if not thetas:
        return {"replicates": [], "meanPred": [], "varPred": [], "meanDiscrepancy": 0.0}
    
    arr = np.array(thetas, dtype=np.float64)
    B, d = arr.shape
    reps = []
    total_disc = 0.0

    for _ in range(n_pred):
        idx = int(seeded_random() * B)
        base = arr[idx]
        
        perturb = (np.array([seeded_random() for _ in range(d)]) - 0.5) * 0.02
        rep = np.clip(base + perturb, 0.0, 1.0)
        s = np.sum(rep) or 1.0
        normed = rep / s
        reps.append(normed)

        disc = np.linalg.norm(base - normed)
        total_disc += disc

    reps_arr = np.array(reps)
    mean_pred = np.mean(reps_arr, axis=0)
    var_pred = np.var(reps_arr, axis=0, ddof=1) if n_pred > 1 else np.zeros(d)

    return {
        "replicates": [[round(float(x), 6) for x in r] for r in reps],
        "meanPred": [round(float(x), 6) for x in mean_pred],
        "varPred": [round(float(x), 8) for x in var_pred],
        "meanDiscrepancy": round(float(total_disc / n_pred), 6)
    }

def _simple_metropolis_hastings(data_mean: float, data_sd: float, n_samples: int, step: float = 0.05) -> list[float]:
    """Run a simple 1D Metropolis-Hastings MCMC sampler with a Gaussian likelihood + weak regularizing prior."""
    samples = []
    current = data_mean
    sd_val = data_sd if data_sd else 0.1
    cur_log_p = -0.5 * ((current - data_mean) / sd_val) ** 2 - abs(current) * 0.5

    for i in range(n_samples + 200):  # +burnin
        prop = current + (seeded_random() - 0.5) * 2.0 * step
        prop_log_p = -0.5 * ((prop - data_mean) / sd_val) ** 2 - abs(prop) * 0.5

        log_a = prop_log_p - cur_log_p
        if log_a > 0.0 or seeded_random() < math.exp(min(0.0, log_a)):
            current = prop
            cur_log_p = prop_log_p
        
        if i >= 200:
            samples.append(round(current, 8))
    return samples

def simulate_posterior(text: str, method: str = 'bootstrap', B: int = 80, dim: int = 8, seed: int | None = None) -> dict[str, Any]:
    """Simulate approximate posterior distributions using bootstrap replicates or Metropolis-Hastings MCMC chains."""
    if seed is not None:
        set_seed(seed)
    used_seed = get_current_seed()
    
    if method == 'mcmc':
        tokens = tokenize(text)
        base_theta = tokens_to_theta(tokens, dim)
        all_chains = []
        summary_mean = []
        summary_sd = []
        esss = []
        for j in range(dim):
            chain = _simple_metropolis_hastings(base_theta[j], 0.15, B, 0.03)
            all_chains.append(chain)
            m = sum(chain) / len(chain)
            v = sum((x - m) ** 2 for x in chain) / max(1, len(chain) - 1)
            summary_mean.append(round(m, 6))
            summary_sd.append(round(math.sqrt(max(0.0, v)), 6))
            esss.append(round(compute_effective_sample_size(chain), 1))
        
        return {
            "method": "mcmc",
            "samples": all_chains,
            "summary": {"mean": summary_mean, "sd": summary_sd},
            "ess": esss
        }

    # Default: bootstrap-as-posterior
    thetas = bootstrap_thetas(text, B, dim, 0.0)
    cis = compute_credible_intervals(thetas)
    return {
        "method": "bootstrap",
        "samples": thetas,
        "summary": {"mean": cis.get("means", []), "sd": cis.get("sds", [])},
        "ess": cis.get("ess", [])
    }

def analyze_corpora(text1: str, text2: str, B_or_config: int | dict = 100, extra_config: dict | None = None) -> dict[str, Any]:
    """
    Main entry point: execute the full comparative analysis pipeline on two corpora.
    Calculates bootstrap/MCMC posteriors, variance metrics, DPC orthogonality gap, and KL divergence.
    """
    dim = 8
    B = 100
    noise_sigma = 0.0
    seed = None
    method = 'bootstrap'
    mcmc_enabled = False

    if isinstance(B_or_config, int):
        B = B_or_config
    elif isinstance(B_or_config, dict):
        B = B_or_config.get("B", 100)
        noise_sigma = B_or_config.get("noiseSigma", 0.0)
        seed = B_or_config.get("seed", None)
        if "method" in B_or_config:
            method = B_or_config["method"]
        if "useMCMC" in B_or_config:
            mcmc_enabled = B_or_config["useMCMC"]

    if extra_config and isinstance(extra_config, dict):
        if "B" in extra_config:
            B = extra_config["B"]
        if "noiseSigma" in extra_config:
            noise_sigma = extra_config["noiseSigma"]
        if "seed" in extra_config:
            seed = extra_config["seed"]
        if "method" in extra_config:
            method = extra_config["method"]
        if "useMCMC" in extra_config:
            mcmc_enabled = extra_config["useMCMC"]

    if seed is not None:
        set_seed(seed)
    used_seed = get_current_seed()

    # Posterior samples
    thetas1 = bootstrap_thetas(text1, B, dim, noise_sigma)
    thetas2 = bootstrap_thetas(text2, B, dim, noise_sigma)

    posterior1 = {"method": "bootstrap", "samples": thetas1}
    posterior2 = {"method": "bootstrap", "samples": thetas2}
    if method == 'mcmc' or mcmc_enabled:
        posterior1 = simulate_posterior(text1, method='mcmc', B=min(B, 120), dim=dim, seed=used_seed)
        posterior2 = simulate_posterior(text2, method='mcmc', B=min(B, 120), dim=dim, seed=used_seed)

    theta_mean1 = tokens_to_theta(tokenize(text1), dim)
    theta_mean2 = tokens_to_theta(tokenize(text2), dim)

    var1 = compute_bootstrap_variance(thetas1)
    var2 = compute_bootstrap_variance(thetas2)
    vdecomp1 = decompose_variance(thetas1)
    vdecomp2 = decompose_variance(thetas2)

    p1 = compute_sentiment_distribution(text1)
    p2 = compute_sentiment_distribution(text2)
    kl = kl_divergence(p1, p2)

    tangent = approximate_tangent_direction(theta_mean1, theta_mean2)
    dpc1 = compute_dpc_gap_with_uncertainty(thetas1, theta_mean1, tangent, 25)
    dpc2 = compute_dpc_gap_with_uncertainty(thetas2, theta_mean2, [-v for v in tangent], 25)
    dpc_gap = round((dpc1["gap"] + dpc2["gap"]) / 2.0, 6)

    credible1 = compute_credible_intervals(thetas1)
    credible2 = compute_credible_intervals(thetas2)
    hdi1 = compute_hdi_credible(thetas1, 0.89)
    hdi2 = compute_hdi_credible(thetas2, 0.89)

    ppc1 = simulate_posterior_predictive(thetas1, 12)
    ppc2 = simulate_posterior_predictive(thetas2, 12)

    result = {
        "bootstrapVariance1": [round(v, 8) for v in var1],
        "bootstrapVariance2": [round(v, 8) for v in var2],
        "klDivergence": round(kl, 6),
        "dpcGap": dpc_gap,
        "dpcDetails": {
            "corpus1": dpc1,
            "corpus2": dpc2,
            "tangentDirection": [round(x, 5) for x in tangent]
        },
        "thetaMean1": [round(x, 5) for x in theta_mean1],
        "thetaMean2": [round(x, 5) for x in theta_mean2],
        "credibleIntervals1": credible1,
        "credibleIntervals2": credible2,
        "B": B,
        "dim": dim,
        "hdi89_1": hdi1,
        "hdi89_2": hdi2,
        "ess1": credible1.get("ess", []),
        "ess2": credible2.get("ess", []),
        "varianceDecomposition1": vdecomp1,
        "varianceDecomposition2": vdecomp2,
        "posteriorPredictive1": {"meanDiscrepancy": ppc1["meanDiscrepancy"], "meanPred": ppc1["meanPred"]},
        "posteriorPredictive2": {"meanDiscrepancy": ppc2["meanDiscrepancy"], "meanPred": ppc2["meanPred"]},
        "posteriorMethod": posterior1["method"],
        "seed": used_seed
    }

    if noise_sigma > 0.0:
        result["noiseSigma"] = noise_sigma
    if mcmc_enabled or method == 'mcmc':
        result["mcmcSummary1"] = posterior1["summary"]
        result["mcmcSummary2"] = posterior2["summary"]
        result["mcmcESS1"] = posterior1["ess"]
        result["mcmcESS2"] = posterior2["ess"]

    result["simulatedPosteriorSummary"] = {
        "method": posterior1["method"],
        "n": B
    }

    return result

def run_self_test(sample_text1: str | None = None, sample_text2: str | None = None) -> dict[str, Any]:
    """Lightweight self-test / invariant validator to ensure mathematical logic is sound."""
    checks = []
    passed = True

    t1 = sample_text1 or 'excellent innovation reliable fast quality success adaptive'
    t2 = sample_text2 or 'mediocre poor negative slow defect disappointment static conservative'

    try:
        toks = tokenize(t1)
        checks.append('tokenize: ' + ('ok' if len(toks) > 0 else 'empty'))

        th = tokens_to_theta(toks)
        sum_th = sum(th)
        sum_ok = abs(sum_th - 1.0) < 1e-6
        checks.append('tokensToTheta L1~1: ' + ('ok' if sum_ok else str(sum_th)))
        if not sum_ok:
            passed = False

        bts = bootstrap_thetas(t1, 8)
        checks.append('bootstrapThetas: n=' + str(len(bts)))

        v = compute_bootstrap_variance(bts)
        all_non_neg = all(x >= 0.0 for x in v)
        checks.append('bootstrapVariance >=0: ' + ('ok' if all_non_neg else 'neg'))
        if not all_non_neg:
            passed = False

        cred = compute_credible_intervals(bts)
        checks.append('credibleIntervals: qs=' + str(len(cred.get("intervals", []))))

        h = compute_hdi_credible(bts)
        checks.append('HDI: ok')

        ess = compute_effective_sample_size([r[0] for r in bts])
        checks.append('ESS: ' + str(ess))

        d = compute_dpc_gap(bts, th, [1.0] + [0.0] * 7)
        dpc_ok = 0.0 <= d["gap"] <= 1.0
        checks.append('DPC in[0,1]: ' + ('ok' if dpc_ok else str(d["gap"])))
        if not dpc_ok:
            passed = False

        vd = decompose_variance(bts)
        checks.append('decomposeVariance trace=' + str(vd["totalTrace"]))

        pp = simulate_posterior_predictive(bts, 5)
        checks.append('PPC discrepancy=' + str(pp["meanDiscrepancy"]))

        post = simulate_posterior(t1, B=6)
        checks.append('simulatePosterior: ' + post["method"])

        kl_test = kl_divergence({"excellent": 0.6}, {"excellent": 0.1})
        checks.append('KL>0: ' + ('ok' if kl_test > 0.0 else str(kl_test)))

        # Repro seed check
        s1 = 424242
        set_seed(s1)
        r1 = bootstrap_thetas(t1, 3, 4, 0.01)
        set_seed(s1)
        r2 = bootstrap_thetas(t1, 3, 4, 0.01)
        repro = r1 == r2
        checks.append('seed repro: ' + ('PASS' if repro else 'FAIL'))
        if not repro:
            passed = False

        res = analyze_corpora(t1, t2, {"B": 12, "seed": 777})
        checks.append('analyzeCorpora seed present: ' + ('ok' if isinstance(res.get("seed"), int) else 'no'))

    except Exception as e:
        checks.append('ERROR: ' + str(e))
        passed = False

    return {"passed": passed, "checks": checks, "nChecks": len(checks)}

def compute_trace_hash(trace: list[str]) -> str:
    """
    Compute the hexadecimal BLAKE3 hash of an agent trace to ensure replay integrity.
    Natively implemented in Python as a fallback.
    """
    h = blake3.blake3()
    for item in trace:
        h.update(item.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()
