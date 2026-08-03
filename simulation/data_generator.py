import numpy as np
import pandas as pd
from scipy import stats

def generate_panel_data(n_periods=30, beta=0.3, q_true=0.08, delta_true=0.6, 
                        lam_start=1000, trend=0.08, noise_sd=0.05, seed=None):
    """
    Generates synthetic panel data representing institutional workload and completions.
    
    Parameters:
        n_periods (int): Number of periods (years/quarters).
        beta (float): True capacity elasticity.
        q_true (float): True error rate (assumed constant).
        delta_true (float): Reviewer detection rate (assumed constant).
        lam_start (float): Starting caseload.
        trend (float): Average growth rate of log-caseload.
        noise_sd (float): Standard deviation of panel noise.
        seed (int): Random seed for reproducibility.
        
    Returns:
        dict: Arrays for caseload, examined, detected, and reported error rate.
    """
    if seed is not None:
        np.random.seed(seed)
        
    # Generate log-caseload as a random walk with trend
    log_lam = np.zeros(n_periods)
    log_lam[0] = np.log(lam_start)
    for t in range(1, n_periods):
        log_lam[t] = log_lam[t-1] + trend + np.random.normal(0, 0.05)
        
    lam = np.exp(log_lam)
    
    # Generate log-examined capacity based on log-caseload and beta
    # kappa = c * lambda^beta * exp(noise)
    # Let c = 8.0, so examined share is around 0.5 for lambda=1000 and beta=0.3
    c = 15.0
    log_kap = np.log(c) + beta * log_lam + np.random.normal(0, noise_sd, n_periods)
    kap = np.exp(log_kap)
    
    # Ensure examined does not exceed caseload
    kap = np.minimum(kap, lam)
    
    # Force float arrays
    lam = np.round(lam).astype(float)
    kap = np.round(kap).astype(float)
    
    # True errors in examined set: T ~ Binomial(examined, q_true)
    # Detected errors: D ~ Binomial(T, delta_true)
    # By property of binomial: D ~ Binomial(examined, q_true * delta_true)
    detected = np.zeros(n_periods)
    for t in range(n_periods):
        detected[t] = float(np.random.binomial(int(kap[t]), q_true * delta_true))
        
    return {
        "year": np.arange(2000, 2000 + n_periods).tolist(),
        "caseload": lam,
        "examined": kap,
        "detected": detected,
        "reported_rate": detected / lam
    }


def generate_capture_recapture_data(n_overlap=2500, q_true=0.08, delta1=0.6, delta2=0.4, 
                                    rho=0.0, seed=None):
    """
    Generates two-screen overlap data, supporting correlated detection capability.
    
    Correlation is modeled using a latent bivariate normal representing reviewer skill/difficulty.
    """
    if seed is not None:
        np.random.seed(seed)
        
    # Generate true error flags for overlap cases
    errors = np.random.binomial(1, q_true, n_overlap)
    n_true_errors = int(errors.sum())
    
    if n_true_errors == 0:
        return {"n11": 0, "n10": 0, "n01": 0, "n_overlap": n_overlap, "n_true": 0}
        
    if rho == 0.0:
        # Independent screens
        s1_detected = np.random.binomial(1, delta1, n_true_errors)
        s2_detected = np.random.binomial(1, delta2, n_true_errors)
    else:
        # Correlated screens: draw latent variables for the true errors
        mean = [0, 0]
        cov = [[1.0, rho], [rho, 1.0]]
        latent = np.random.multivariate_normal(mean, cov, n_true_errors)
        
        # Convert thresholds using inverse CDF of standard normal
        thresh1 = stats.norm.ppf(delta1)
        thresh2 = stats.norm.ppf(delta2)
        
        # Detect if latent skill is below threshold (positive correlation in failures)
        # Note: to align with the positive correlation of "difficulty",
        # if a case is hard (low latent draw), both are likely to miss.
        # So we flag detection if latent draw is less than thresh.
        s1_detected = (latent[:, 0] < thresh1).astype(int)
        s2_detected = (latent[:, 1] < thresh2).astype(int)
        
    n11 = int(np.sum((s1_detected == 1) & (s2_detected == 1)))
    n10 = int(np.sum((s1_detected == 1) & (s2_detected == 0)))
    n01 = int(np.sum((s1_detected == 0) & (s2_detected == 1)))
    
    return {
        "n11": n11,
        "n10": n10,
        "n01": n01,
        "n_overlap": n_overlap,
        "n_true": n_true_errors
    }


def generate_three_screen_data(n_overlap=5000, q_true=0.10, deltas=(0.55, 0.40, 0.30), 
                              seed=None):
    """
    Generates three independent screens data for log-linear estimation.
    """
    if seed is not None:
        np.random.seed(seed)
        
    errors = np.random.binomial(1, q_true, n_overlap)
    n_true = int(errors.sum())
    
    s1 = np.random.binomial(1, deltas[0], n_true)
    s2 = np.random.binomial(1, deltas[1], n_true)
    s3 = np.random.binomial(1, deltas[2], n_true)
    
    counts = {}
    patterns = ['111', '110', '101', '011', '100', '010', '001']
    for p in patterns:
        counts[p] = 0
        
    for i in range(n_true):
        pat = f"{s1[i]}{s2[i]}{s3[i]}"
        if pat != '000':
            counts[pat] += 1
            
    return counts
