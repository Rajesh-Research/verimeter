import numpy as np

def compute_adf_resid_t(resid, maxlag=1):
    """
    Computes the Dickey-Fuller t-statistic on regression residuals (no constant in secondary step).
    """
    resid = np.asarray(resid, dtype=float)
    dx = np.diff(resid)
    n = len(dx)
    if n < 8:
        return np.nan
        
    # Standard residual DF has lagged residuals and lagged differences (for ADF)
    # The regressor matrix contains: lagged residual (x_{t-1}) and lag differences
    cols = [resid[:n]]
    for L in range(1, min(maxlag, max(n // 4, 1)) + 1):
        lag = np.r_[np.zeros(L), dx[:-L]] if L < n else np.zeros(n)
        cols.append(lag[:n])
    X = np.column_stack(cols)
    
    try:
        # Fit OLS: dy = beta * y_{t-1} + lags
        beta, *_ = np.linalg.lstsq(X, dx, rcond=None)
    except np.linalg.LinAlgError:
        return np.nan
        
    r = dx - X @ beta
    dof = max(n - X.shape[1], 1)
    s2 = float(r @ r) / dof
    XtX = np.linalg.pinv(X.T @ X)
    se = float(np.sqrt(max(s2 * XtX[0, 0], 0.0)))
    
    if se <= 0:
        return np.nan
    return float(beta[0] / se)


def get_engle_granger_critical(n, level=0.05):
    """
    Calculates Engle-Granger response surface critical values for one regressor 
    and constant. 
    
    These critical values are much more negative than Dickey-Fuller values 
    because the unit-root test is applied to ESTIMATED residuals, which minimizes 
    residual variance by design.
    """
    coef = {
        0.01: (-3.9001, -10.534, -30.03),
        0.05: (-3.3377, -5.967, -8.98),
        0.10: (-3.0462, -4.069, -5.73)
    }
    a, b, c = coef.get(level, coef[0.05])
    n = max(int(n), 10)
    return a + b / n + c / n ** 2
