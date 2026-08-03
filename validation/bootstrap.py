import numpy as np

def bootstrap_se(df, estimator_func, n_boot=200, seed=42):
    """
    Computes standard error of an estimator using panel block bootstrapping.
    """
    np.random.seed(seed)
    estimates = []
    n = len(df)
    
    for i in range(n_boot):
        # Resample indices with replacement
        idx = np.random.choice(n, size=n, replace=True)
        resampled_df = df.iloc[idx].reset_index(drop=True)
        try:
            val = estimator_func(resampled_df)
            if np.isfinite(val):
                estimates.append(val)
        except:
            pass
            
    if len(estimates) < 10:
        return np.nan
        
    return float(np.std(estimates, ddof=1))


def jackknife_se(df, estimator_func):
    """
    Computes standard error of an estimator using leave-one-out Jackknife resampling.
    """
    estimates = []
    n = len(df)
    
    for i in range(n):
        # Exclude index i
        idx = [j for j in range(n) if j != i]
        resampled_df = df.iloc[idx].reset_index(drop=True)
        try:
            val = estimator_func(resampled_df)
            if np.isfinite(val):
                estimates.append(val)
        except:
            pass
            
    if len(estimates) < 3:
        return np.nan
        
    mean_est = np.mean(estimates)
    var = ((n - 1) / n) * np.sum((np.array(estimates) - mean_est) ** 2)
    return float(np.sqrt(max(var, 0.0)))
