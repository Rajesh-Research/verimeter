import numpy as np
from scipy import stats

from verimeter.stats.regression import fit_ols, compute_hac_se
from verimeter.stats.capture_recapture import estimate_two_screen

def monte_carlo_validation(n_replicates=100, n_periods=30, beta_true=0.3, q_true=0.08, 
                           delta_true=0.6, seed=42):
    """
    Runs Monte Carlo simulation to evaluate parameter recovery.
    """
    np.random.seed(seed)
    
    recovered_betas = []
    recovered_qs = []
    
    for i in range(n_replicates):
        # 1. Generate OLS log-panel
        # Log caseload lambda is a random walk with trend
        log_lam = np.zeros(n_periods)
        log_lam[0] = np.log(1000.0)
        for t in range(1, n_periods):
            log_lam[t] = log_lam[t-1] + 0.08 + np.random.normal(0, 0.05)
        lam = np.exp(log_lam)
        
        # Log capacity kappa
        log_kap = np.log(15.0) + beta_true * log_lam + np.random.normal(0, 0.05, n_periods)
        kap = np.minimum(np.exp(log_kap), lam)
        
        fit = fit_ols(np.log(lam), np.log(kap))
        recovered_betas.append(fit["slope"])
        
        # 2. Generate capture-recapture count overlap
        n_overlap = 3000
        errors = np.random.binomial(1, q_true, n_overlap)
        n_true = int(errors.sum())
        
        s1 = np.random.binomial(1, delta_true, n_true)
        s2 = np.random.binomial(1, 0.40, n_true)  # assume screen 2 delta = 0.40
        
        n11 = int(np.sum((s1 == 1) & (s2 == 1)))
        n10 = int(np.sum((s1 == 1) & (s2 == 0)))
        n01 = int(np.sum((s1 == 0) & (s2 == 1)))
        
        try:
            est = estimate_two_screen(n11, n10, n01, n_overlap)
            recovered_qs.append(est["q"])
        except:
            pass
            
    return {
        "beta_mean": float(np.mean(recovered_betas)),
        "beta_sd": float(np.std(recovered_betas)),
        "beta_mse": float(np.mean((np.array(recovered_betas) - beta_true) ** 2)),
        "q_mean": float(np.mean(recovered_qs)),
        "q_sd": float(np.std(recovered_qs)),
        "q_mse": float(np.mean((np.array(recovered_qs) - q_true) ** 2))
    }


def compute_elasticity_power(n_periods=30, beta_null=1.0, beta_alt=0.5, 
                             n_replicates=200, alpha=0.05, seed=42):
    """
    Computes statistical power to reject H0: beta = beta_null when true beta = beta_alt.
    """
    np.random.seed(seed)
    rejections = 0
    
    for i in range(n_replicates):
        log_lam = np.zeros(n_periods)
        log_lam[0] = np.log(1000.0)
        for t in range(1, n_periods):
            log_lam[t] = log_lam[t-1] + 0.08 + np.random.normal(0, 0.05)
            
        log_kap = np.log(15.0) + beta_alt * log_lam + np.random.normal(0, 0.05, n_periods)
        lam = np.exp(log_lam)
        kap = np.minimum(np.exp(log_kap), lam)
        
        fit = fit_ols(np.log(lam), np.log(kap))
        se = compute_hac_se(np.log(lam), fit["residuals"])
        if not np.isfinite(se) or se <= 0:
            se = fit["stderr"]
            
        t_stat = (fit["slope"] - beta_null) / se
        p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n_periods - 2))
        
        if p_val < alpha:
            rejections += 1
            
    return {
        "power": rejections / n_replicates,
        "n_periods": n_periods,
        "beta_null": beta_null,
        "beta_alt": beta_alt
    }
