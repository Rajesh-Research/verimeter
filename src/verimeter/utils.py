import numpy as np
from scipy import stats

def _adf(x, maxlag=1):
    """
    Computes the Dickey-Fuller t-statistic for lag 1 (used for Engle-Granger residual test).
    
    Parameters:
        x (array_like): 1D array of residuals.
        maxlag (int): lag count.
        
    Returns:
        float: t-statistic.
        None: placeholder.
    """
    x = np.asarray(x, float)
    dx = np.diff(x)
    n = len(dx)
    if n < 8:
        return np.nan, None
    cols = [x[:n], np.ones(n)]
    for L in range(1, min(maxlag, max(n // 4, 1)) + 1):
        lag = np.r_[np.zeros(L), dx[:-L]] if L < n else np.zeros(n)
        cols.append(lag[:n])
    X = np.column_stack(cols)
    try:
        beta, *_ = np.linalg.lstsq(X, dx, rcond=None)
    except np.linalg.LinAlgError:
        return np.nan, None
    resid = dx - X @ beta
    dof = max(n - X.shape[1], 1)
    s2 = float(resid @ resid) / dof
    XtX = np.linalg.pinv(X.T @ X)
    se = float(np.sqrt(max(s2 * XtX[0, 0], 0.0)))
    if se <= 0:
        return np.nan, None
    t = float(beta[0] / se)
    return t, None


def _eg_critical(n, level=0.05):
    """
    Engle-Granger critical values for a residual-based cointegration test with
    one regressor and a constant. Uses response-surface approximations.
    
    Using standard Dickey-Fuller critical values here is a major error because the 
    residuals are estimated rather than observed.
    """
    coef = {
        0.01: (-3.9001, -10.534, -30.03),
        0.05: (-3.3377, -5.967, -8.98),
        0.10: (-3.0462, -4.069, -5.73)
    }
    a, b, c = coef.get(level, coef[0.05])
    n = max(int(n), 10)
    return a + b / n + c / n ** 2


def _hac_se(x, resid, nlags=None):
    """
    Computes Newey-West Heteroskedasticity and Autocorrelation Consistent (HAC) standard error
    for the slope parameter in OLS regression.
    """
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
