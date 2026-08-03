import warnings
import numpy as np
from scipy import stats, optimize

def estimate_two_screen(n11, n10, n01, n_overlap, alpha=0.05):
    """
    Implements the Chapman-corrected two-screen capture-recapture estimator.
    
    Incorporates the high-severity fix D5:
    Combines conditional Chapman variance and binomial variance components.
    """
    for nm, v in (("n11", n11), ("n10", n10), ("n01", n01)):
        if v < 0 or int(v) != v:
            raise ValueError(f"{nm} must be a non-negative integer")
    if n11 + n10 + n01 > n_overlap:
        raise ValueError("detected errors exceed the overlap")
    if n11 == 0:
        raise ValueError("no errors found by both screens; delta is not estimable. Widen the overlap window.")
        
    notes = []
    if n11 < 7:
        notes.append(f"n11 = {n11}; coverage is poor below ~7 joint detections.")
        
    n1_ = n11 + n10  # flagged by screen 1
    n_1 = n11 + n01  # flagged by screen 2
    
    # Chapman unbiased estimate of true error count N
    N = (n1_ + 1) * (n_1 + 1) / (n11 + 1) - 1
    
    # Reviewer depths (detection probabilities)
    d1 = n11 / n_1
    d2 = n11 / n1_
    
    # Wilson interval for screen 1 depth (since depth is binomial relative to true errors n_1)
    z = stats.norm.ppf(1 - alpha / 2)
    den = 1 + z ** 2 / n_1
    ctr = (d1 + z ** 2 / (2 * n_1)) / den
    half = z * np.sqrt(d1 * (1 - d1) / n_1 + z ** 2 / (4 * n_1 ** 2)) / den
    d1_ci = (max(ctr - half, 0.0), min(ctr + half, 1.0))
    
    # Hardened standard error: Chapman conditional variance of N + Binomial variance of true N
    # var(N) = var(N | true_N) + var(true_N)
    var_cond = ((n1_ + 1) * (n_1 + 1) * (n1_ - n11) * (n_1 - n11)
                / ((n11 + 1) ** 2 * (n11 + 2)))
    
    q_hat = N / n_overlap
    var_binom = n_overlap * q_hat * (1 - q_hat)
    
    # Total SE on the rate scale
    se_tot = float(np.sqrt(max(var_cond, 0.0) + max(var_binom, 0.0))) / n_overlap
    se_cond = float(np.sqrt(max(var_cond, 0.0)))
    
    q_ci = (max(q_hat - z * se_tot, 0.0), min(q_hat + z * se_tot, 1.0))
    
    if N > n_overlap:
        notes.append("estimated errors exceed the overlap; screens strongly dependent. q is a lower bound only.")
    notes.append("independence ASSUMED not tested: 3 cells, 3 parameters, 0 df. Under positive dependence q is a LOWER BOUND. See dependence_bound().")
    
    return {
        "delta1": d1,
        "delta2": d2,
        "delta1_ci": d1_ci,
        "q": q_hat,
        "q_ci": q_ci,
        "n_true_errors": N,
        "se_conditional": se_cond,
        "se_total": se_tot * n_overlap,  # kept on count scale for display API compatibility
        "n_overlap": n_overlap,
        "notes": notes
    }


def compute_dependence_bound(q_hat, rho_grid=(0.0, 0.3, 0.6, 0.9)) -> dict:
    """
    Supplies sensitivity multipliers for capture-recapture rates under screen dependence (rho).
    """
    mult = {0.0: 1.000, 0.3: 1.055, 0.6: 1.247, 0.9: 1.616}
    return {
        "bounds": {r: q_hat * mult[r] for r in rho_grid if r in mult},
        "note": ("q_hat is a lower bound. Multipliers from simulation of a shared "
                 "case-difficulty factor (n=4000, q=0.10, delta=(0.55,0.40)); "
                 "understatement 0%, 5.2%, 19.8%, 38.1% at rho = 0, .3, .6, .9.")
    }


def estimate_three_screen(counts: dict, n_overlap, alpha=0.05) -> dict:
    """
    Fits a Poisson log-linear capture-recapture model on a three-screen setup.
    
    Incorporates the high-severity fix D7:
    Correctly uses df = 3 (7 cells - 4 parameters = 3 degrees of freedom) 
    for the independence deviance chi-square test.
    """
    pat = ['111', '110', '101', '011', '100', '010', '001']
    y = np.array([float(counts.get(p, 0)) for p in pat])
    
    if y.sum() < 20:
        warnings.warn("fewer than 20 detected errors; estimates unstable")
        
    # Design matrix: columns are Intercept, S1, S2, S3
    X = np.array([[1.0, float(p[0]), float(p[1]), float(p[2])] for p in pat])
    
    def negll(b):
        mu = np.exp(np.clip(X @ b, -50, 50))
        return float(np.sum(mu - y * np.log(np.maximum(mu, 1e-300))))
        
    best = None
    for s0 in (np.zeros(4), np.array([1., 0., 0., 0.]), np.array([2., .5, .5, .5])):
        r = optimize.minimize(negll, s0, method="Nelder-Mead",
                              options=dict(maxiter=40000, maxfev=40000,
                                           fatol=1e-12, xatol=1e-12))
        if best is None or r.fun < best.fun:
            best = r
            
    b = best.x
    mu = np.exp(np.clip(X @ b, -50, 50))
    n000 = float(np.exp(np.clip(b[0], -50, 50)))
    N = float(y.sum() + n000)
    
    # Deviance = 2 * sum( y * log(y/mu) - (y - mu) )
    dev = 2 * float(np.sum(np.where(y > 0, y * np.log(y / np.maximum(mu, 1e-300)), 0.0) - (y - mu)))
    
    # df = 7 cells - 4 params = 3 degrees of freedom
    df = len(pat) - X.shape[1]
    p_ind = float(1 - stats.chi2.cdf(max(dev, 0.0), df))
    
    # Estimated depths
    d = [float(sum(v for k, v in counts.items() if k[i] == '1') / N) for i in range(3)]
    
    return {
        "N_true": N,
        "q": N / n_overlap,
        "delta": d,
        "n_missed": n000,
        "deviance": dev,
        "df": df,
        "p_independence": p_ind,
        "independence_rejected": bool(p_ind < 0.05),
        "converged": bool(best.success),
        "note": ("independence REJECTED (df=3); two-screen would be biased"
                 if p_ind < 0.05 else
                 "independence not rejected at 5% (df=3)")
    }


def compute_overlap_required(delta_from, delta_to, q, power=0.80, alpha=0.05) -> dict:
    """
    Computes overlap sample sizes needed to power a capture-recapture diagnostic study.
    """
    za, zb = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    pb = (delta_from + delta_to) / 2
    n_err = ((za * np.sqrt(2 * pb * (1 - pb))
              + zb * np.sqrt(delta_from * (1 - delta_from)
                             + delta_to * (1 - delta_to))) ** 2
             / (delta_from - delta_to) ** 2)
    return {
        "caught_error_pairs": int(np.ceil(n_err)),
        "overlap_cases": int(np.ceil(n_err / max(q, 1e-9))),
        "note": f"assumes true error rate q = {q:.4f}"
    }
