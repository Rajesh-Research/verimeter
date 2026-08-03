import numpy as np
from scipy import stats

def fit_ols(x, y):
    """
    Fits a simple OLS linear regression: y = intercept + slope * x.
    
    Returns:
        dict: slope, intercept, r_value, stderr, residuals
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    res = stats.linregress(x, y)
    resid = y - (res.intercept + res.slope * x)
    return {
        "slope": float(res.slope),
        "intercept": float(res.intercept),
        "r_value": float(res.rvalue),
        "r_squared": float(res.rvalue ** 2),
        "stderr": float(res.stderr),
        "residuals": resid
    }


def compute_hac_se(x, resid, nlags=None):
    """
    Computes Newey-West Heteroskedasticity and Autocorrelation Consistent (HAC) standard error
    for the slope parameter of an OLS regression.
    
    Uses Bartlett kernel weights: w_j = 1 - j / (nlags + 1).
    """
    x = np.asarray(x, dtype=float)
    resid = np.asarray(resid, dtype=float)
    n = len(x)
    
    if nlags is None:
        nlags = max(1, int(np.floor(4 * (n / 100.0) ** (2.0 / 9.0))))
        
    xc = x - x.mean()
    Sxx = float(xc @ xc)
    if Sxx <= 0:
        return np.nan
        
    u = xc * resid
    S = float(u @ u)
    for L in range(1, min(nlags, n - 1) + 1):
        w = 1.0 - L / (nlags + 1.0)
        S += 2.0 * w * float(u[L:] @ u[:-L])
    S = max(S, 0.0)
    return float(np.sqrt(S) / Sxx)


def compute_outlier_diagnostics(x, y):
    """
    Computes Cook's Distance and DFBETAS values for OLS regression.
    
    - Cook's Distance measures overall influence of period i on the OLS fit.
    - DFBETAS measures change in the slope coefficient when period i is excluded.
    
    Returns:
        dict: cooks_d (array), dfbetas (array), leverage (array)
    """
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    n = len(x)
    if n < 3:
        return {"cooks_d": np.zeros(n), "dfbetas": np.zeros(n), "leverage": np.zeros(n)}
        
    # Fit full model
    full = fit_ols(x, y)
    beta_full = full["slope"]
    resid = full["residuals"]
    
    # Variance of residuals
    s2 = np.sum(resid ** 2) / (n - 2)
    s2 = max(s2, 1e-12)
    
    # Compute leverage (hat matrix diagonal)
    xc = x - x.mean()
    sum_xc2 = np.sum(xc ** 2)
    if sum_xc2 <= 0:
        leverage = np.ones(n) / n
    else:
        leverage = 1.0 / n + (xc ** 2) / sum_xc2
        
    # Cook's distance
    # D_i = e_i^2 * h_i / (2 * s^2 * (1 - h_i)^2)
    denom = 2 * s2 * ((1.0 - leverage) ** 2)
    cooks_d = (resid ** 2) * leverage / np.maximum(denom, 1e-15)
    
    # DFBETAS for slope
    # dfbeta_i = (beta - beta_(i)) / se(beta)
    # Formally, dfbeta_i = e_i * x_c_i / ( (1 - h_i) * sum_xc2 )
    # DFBETAS divides this by the standard error of beta calculated without observation i
    dfbetas = np.zeros(n)
    for i in range(n):
        # Exclude i
        x_sub = np.delete(x, i)
        y_sub = np.delete(y, i)
        sub_fit = fit_ols(x_sub, y_sub)
        beta_i = sub_fit["slope"]
        
        # Calculate sub stderr
        sub_resid = sub_fit["residuals"]
        sub_s2 = np.sum(sub_resid ** 2) / (n - 3)
        sub_s2 = max(sub_s2, 1e-12)
        sub_xc = x_sub - x_sub.mean()
        sub_sum_xc2 = np.sum(sub_xc ** 2)
        
        if sub_sum_xc2 > 0:
            se_beta_i = np.sqrt(sub_s2 / sub_sum_xc2)
            dfbetas[i] = (beta_full - beta_i) / max(se_beta_i, 1e-9)
            
    return {
        "cooks_d": cooks_d,
        "dfbetas": dfbetas,
        "leverage": leverage
    }


def correct_measurement_error(beta_hat, x, se_hat, meas_error_sd):
    """
    Applies classical Errors-in-Variables (EIV) slope adjustment.
    
    Returns:
        dict: beta_corrected, reliability, inflation, se_corrected, note
    """
    x = np.asarray(x, dtype=float)
    var_x = float(np.var(x, ddof=1))
    var_u = float(meas_error_sd ** 2)
    
    if var_u >= var_x:
        return {
            "beta_corrected": float("nan"),
            "se_corrected": float("nan"),
            "reliability": 0.0,
            "inflation": float("nan"),
            "note": "Assumed measurement error exceeds observed variance; beta is not identified."
        }
        
    reliability = 1.0 - var_u / var_x
    beta_corrected = beta_hat / reliability
    se_corrected = se_hat / reliability
    inflation = 1.0 / reliability
    
    return {
        "beta_corrected": beta_corrected,
        "se_corrected": se_corrected,
        "reliability": reliability,
        "inflation": inflation,
        "note": (f"with measurement-error sd {meas_error_sd:.2f} in log caseload, "
                 f"true beta is about {beta_corrected:.3f}, not {beta_hat:.3f}. "
                 "Attenuation runs toward the inversion finding, so the uncorrected "
                 "estimate overstates the case.")
    }
