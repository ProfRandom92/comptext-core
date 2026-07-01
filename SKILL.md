---
name: stochastic_validation
description: Playbook for running stochastic DPC-Gap, MCMC, and trace integrity validations on CompText/pCompText.
context: fork
---

# Stochastic Validation Playbook

This skill provides behavioral instructions, diagnostics, and playbooks for executing stochastic calculations, DPC-Gap metrics, Metropolis-Hastings MCMC, and trace integrity validations.

## 1. Mathematical Rules & Playbook

When utilizing the `pcomptext` statistical engine, the agent MUST adhere to the following formal parameters:

### A. Quantile Credible Intervals (ETI) & Highest Density Intervals (HDI)
*   **Equal-Tailed Credible Interval (ETI)**: Computed at standard quantiles $q = [0.025, 0.5, 0.975]$. Used to inspect general stochastic distribution spread.
*   **Highest Density Interval (HDI)**: Evaluated at standard $89\%$ probability mass. The agent MUST identify the minimum width window containing $89\%$ of the bootstrap distribution:
    $$\text{HDI} = \arg\min_{[a, b]} (b - a) \quad \text{s.t.} \quad P(\theta \in [a, b]) \ge 0.89$$

### B. Effective Sample Size (ESS) Diagnostics
*   Ensure MCMC chain convergence using AR(1) autocorrelation:
    $$\rho_1 = \frac{\sum_{t=2}^N (x_t - \mu)(x_{t-1} - \mu)}{\sum_{t=1}^N (x_t - \mu)^2}$$
    $$\text{ESS} = N \frac{1 - \rho_1}{1 + \rho_1}$$
*   **Action Boundary**: If estimated ESS falls below $30.0$ per dimension, the agent MUST flag the chain as "unconverged" and recommend increasing replicates $B$ or tuning step size.

### C. Shannon KL-Divergenz & Regularization
*   Always apply Dirichlet regularization to avoid zero counts in vocabulary distribution slots.
*   The KL-Divergence calculation uses $10^{-12}$ base floor to guarantee numerical stability:
    $$D_{\text{KL}}(P \parallel Q) = \sum_{i=1}^d P_i \log \left( \frac{P_i}{\max(Q_i, 10^{-12})} \right)$$

### D. Dynamic Probabilistic Consistency (DPC) Gap
*   Align the bootstrap variance direction $\vec{v}_{\text{dir}}$ with the tangent vector $\vec{t}$:
    $$\text{DPC-Gap} = \left| \vec{v}_{\text{dir}} \cdot \vec{t} \right|$$
*   **Asymptotics**: The DPC-Gap values must strictly reside in $[0, 1]$. Values approaching $0.0$ represent ideal orthogonal alignment on the latent manifold.

## 2. Replay & Trace Integrity
*   Prior to promotion of any agent trace logs or execution records, the agent MUST calculate the BLAKE3 trace hash using `verify_trace_integrity` to secure structural replay-ability.
