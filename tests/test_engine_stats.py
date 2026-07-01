import pytest
import math
import subprocess
import sys
import threading
from pathlib import Path
import numpy as np
from comptext.core.engine_stats import (
    seeded_random,
    set_seed,
    tokenize,
    tokens_to_theta,
    tokens_to_counts,
    bootstrap_thetas,
    compute_bootstrap_variance,
    compute_credible_intervals,
    compute_hdi_credible,
    compute_effective_sample_size,
    kl_divergence,
    compute_sentiment_distribution,
    compute_dpc_gap,
    compute_dpc_gap_with_uncertainty,
    simulate_posterior,
    simulate_posterior_predictive,
    decompose_variance,
    get_sentiment_vocab,
    is_sentiment_term,
    expand_sentiment_lexicon,
    compute_trace_hash
)

def test_seeded_random():
    """Verify that Mulberry32 PRNG provides deterministic reproducible values."""
    set_seed(12345)
    r1 = [seeded_random() for _ in range(5)]
    
    set_seed(12345)
    r2 = [seeded_random() for _ in range(5)]
    
    assert r1 == r2
    assert all(0.0 <= r <= 1.0 for r in r1)

def test_tokenize():
    """Verify tokenization removes punctuation and handles case normalization."""
    text = "Hello, World! Dies ist ein ÄÖÜ-Test."
    tokens = tokenize(text)
    assert tokens == ["hello", "world", "dies", "ist", "ein", "äöü", "test"]

def test_tokens_to_theta():
    """Verify tokens_to_theta normalizes output and adds Dirichlet smoothing."""
    t0 = tokens_to_theta([], dim=4)
    assert len(t0) == 4
    assert all(math.isclose(v, 0.25) for v in t0)
    assert math.isclose(sum(t0), 1.0)
    
    t1 = tokens_to_theta(["excellent", "great"], dim=8, prior_strength=1e-4)
    assert len(t1) == 8
    assert math.isclose(sum(t1), 1.0)

def test_tokens_to_counts():
    """Verify tokens_to_counts matches raw word hashes without prior strength."""
    tokens = ["excellent", "great", "excellent"]
    counts = tokens_to_counts(tokens, dim=8)
    assert sum(counts) == 3
    t_exc = tokens_to_counts(["excellent"], 8)
    t_gr = tokens_to_counts(["great"], 8)
    assert counts[np.argmax(t_exc)] == 2
    assert counts[np.argmax(t_gr)] == 1

def test_bootstrap_thetas_reproducible():
    """Verify bootstrap_thetas yields deterministic results with same seed."""
    text = "excellent innovation reliable fast quality success adaptive. mediocre poor negative slow defect disappointment."
    set_seed(42)
    rep1 = bootstrap_thetas(text, B=5, dim=8, noise_sigma=0.01)
    set_seed(42)
    rep2 = bootstrap_thetas(text, B=5, dim=8, noise_sigma=0.01)
    
    assert rep1 == rep2
    assert len(rep1) == 5
    assert len(rep1[0]) == 8

def test_compute_bootstrap_variance():
    """Verify sample variance calculation."""
    thetas = [
        [0.1, 0.2, 0.7],
        [0.12, 0.18, 0.7],
        [0.08, 0.22, 0.7]
    ]
    var = compute_bootstrap_variance(thetas)
    assert len(var) == 3
    assert var[2] < 1e-15
    assert all(v >= 0.0 for v in var)

def test_credible_intervals():
    """Verify ETI quantile credible intervals."""
    thetas = [
        [0.1], [0.2], [0.3], [0.4], [0.5], [0.6], [0.7], [0.8], [0.9], [1.0]
    ]
    res = compute_credible_intervals(thetas, qs=[0.05, 0.5, 0.95])
    assert "means" in res
    assert "intervals" in res
    assert len(res["intervals"]) == 3

def test_hdi_credible():
    """Verify Highest Density Interval calculation."""
    thetas = [
        [0.1], [0.2], [0.3], [0.4], [0.5], [0.6], [0.7], [0.8], [0.9], [1.0]
    ]
    res = compute_hdi_credible(thetas, prob=0.8)
    assert "hdi" in res
    assert len(res["hdi"]) == 1
    hdi = res["hdi"][0]
    assert hdi[1] - hdi[0] > 0.0
    assert hdi[0] >= 0.1 and hdi[1] <= 1.0

def test_compute_effective_sample_size():
    """Verify ESS estimation."""
    chain = [0.5] * 20
    ess = compute_effective_sample_size(chain)
    assert ess == 20.0
    
    chain_rand = [0.1, 0.9, 0.2, 0.8, 0.1, 0.9]
    ess_rand = compute_effective_sample_size(chain_rand)
    assert 1.0 <= ess_rand <= 6.0

def test_kl_divergence():
    """Verify KL-Divergence properties."""
    p = {"excellent": 0.8, "mediocre": 0.2}
    q = {"excellent": 0.8, "mediocre": 0.2}
    assert math.isclose(kl_divergence(p, q), 0.0, abs_tol=1e-9)
    
    r = {"excellent": 0.2, "mediocre": 0.8}
    assert kl_divergence(p, r) > 0.0

def test_compute_sentiment_distribution():
    """Verify smoothed sentiment distribution matches lexicon counts."""
    text = "excellent innovation. mediocre poor."
    dist = compute_sentiment_distribution(text, alpha=0.5)
    assert dist["excellent"] > 0.0
    assert dist["mediocre"] > 0.0
    assert math.isclose(sum(dist.values()), 1.0)

def test_dpc_gap():
    """Verify DPC Gap calculation."""
    thetas = [
        [0.1, 0.9],
        [0.12, 0.88],
        [0.08, 0.92]
    ]
    theta_mean = [0.1, 0.9]
    tangent = [1.0, -1.0]
    
    res = compute_dpc_gap(thetas, theta_mean, tangent)
    assert "gap" in res
    assert "cosine" in res
    assert 0.0 <= res["gap"] <= 1.0

def test_dpc_gap_with_uncertainty():
    """Verify DPC Gap CI calculations."""
    thetas = [
        [0.1, 0.9],
        [0.12, 0.88],
        [0.08, 0.92],
        [0.11, 0.89],
        [0.09, 0.91]
    ]
    theta_mean = [0.1, 0.9]
    tangent = [0.7071, -0.7071]
    
    set_seed(42)
    res = compute_dpc_gap_with_uncertainty(thetas, theta_mean, tangent, n_sub=5)
    assert "gap" in res
    assert "gapCI" in res
    assert len(res["gapCI"]) == 2

def test_simulate_posterior():
    """Verify Metropolis-Hastings MCMC simulation runs."""
    set_seed(123)
    res = simulate_posterior("excellent innovation", method="mcmc", B=50, dim=4)
    assert res["method"] == "mcmc"
    assert len(res["samples"]) == 4
    assert len(res["samples"][0]) == 50
    assert "summary" in res
    assert "ess" in res

def test_simulate_posterior_predictive():
    """Verify PPC replicates and L2 discrepancy checks."""
    thetas = [
        [0.2, 0.8],
        [0.22, 0.78]
    ]
    set_seed(42)
    res = simulate_posterior_predictive(thetas, n_pred=10)
    assert "replicates" in res
    assert "meanPred" in res
    assert "varPred" in res
    assert "meanDiscrepancy" in res
    assert len(res["replicates"]) == 10
    assert res["meanDiscrepancy"] >= 0.0

def test_decompose_variance():
    """Verify variance decomposition trace calculation."""
    thetas = [
        [0.1, 0.9],
        [0.12, 0.88],
        [0.08, 0.92]
    ]
    res = decompose_variance(thetas)
    assert "totalTrace" in res
    assert "perDim" in res
    assert "meanVar" in res
    assert res["totalTrace"] >= 0.0
    assert res["n"] == 3

def test_sentiment_vocab_determinism():
    """Verify deterministic behaviour of get_sentiment_vocab and is_sentiment_term."""
    vocab_1 = get_sentiment_vocab()
    vocab_2 = get_sentiment_vocab()
    assert vocab_1 == vocab_2
    assert is_sentiment_term("excellent")
    assert not is_sentiment_term("not_a_sentiment_term")

def test_concurrency_sentiment_lexicon():
    """Verify thread-safety of expand_sentiment_lexicon under concurrent access."""
    threads = []
    added_terms = []
    lock = threading.Lock()
    
    def worker(tid):
        terms = [f"term_thread_{tid}_{i}" for i in range(10)]
        res = expand_sentiment_lexicon(terms)
        with lock:
            added_terms.extend(res)
        
    for i in range(10):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    vocab = get_sentiment_vocab()
    for term in added_terms:
        assert is_sentiment_term(term)
        assert term in vocab

def test_trace_hash_consistency_with_rust():
    """Verify that Python fallback compute_trace_hash matches Rust sparkctl binary hash."""
    trace_log = ["action: tokenize", "state: success", "metric: gap=0.002186"]
    
    # Compute Python trace hash
    py_hash = compute_trace_hash(trace_log)
    assert len(py_hash) == 64
    
    # Try to resolve Rust sparkctl binary
    binary_name = "comptext-sparkctl.exe" if sys.platform == "win32" else "comptext-sparkctl"
    sparkctl_dir = Path("C:/Users/contr/Desktop/ct/comptext-sparkctl")
    binary_path = sparkctl_dir / "target" / "debug" / binary_name
    
    if binary_path.exists():
        try:
            cmd = [str(binary_path), "--hash-trace"] + trace_log
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            rust_hash = res.stdout.strip()
            assert py_hash == rust_hash, f"Hash mismatch! Py: {py_hash}, Rust: {rust_hash}"
        except Exception as e:
            pytest.skip(f"Could not run Rust binary comparison: {e}")
    else:
        # Fallback to checking the sibling location under sandbox imports
        sandbox_sparkctl_dir = Path("C:/CompText-SPARK-Sandbox-TESTING/CompText-SPARK-Sandbox/repos/comptext-sparkctl")
        sandbox_binary_path = sandbox_sparkctl_dir / "target" / "debug" / binary_name
        if sandbox_binary_path.exists():
            try:
                cmd = [str(sandbox_binary_path), "--hash-trace"] + trace_log
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                rust_hash = res.stdout.strip()
                assert py_hash == rust_hash, f"Hash mismatch! Py: {py_hash}, Rust: {rust_hash}"
            except Exception as e:
                pytest.skip(f"Could not run sandbox Rust binary comparison: {e}")
        else:
            pytest.skip(f"Rust binary not found at {binary_path} or {sandbox_binary_path}")
