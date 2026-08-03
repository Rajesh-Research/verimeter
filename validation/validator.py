import numpy as np

def validate_panel(year, caseload, examined, detected):
    """
    Validates a panel dataset to ensure consistency and prevent spurious outputs.
    
    Returns:
        list of str: Found validation issues. Empty list means the panel is fully valid.
    """
    errors = []
    n = len(year)
    
    if n < 8:
        errors.append(f"Panel contains only {n} periods; capacity elasticity requires at least 8 periods for cointegration testing.")
        
    for name, series in [("caseload", caseload), ("examined", examined), ("detected", detected)]:
        if len(series) != n:
            errors.append(f"Series '{name}' length ({len(series)}) does not match panel length ({n}).")
        
        # Check for NaNs and infinities
        series_arr = np.asarray(series, dtype=float)
        if not np.all(np.isfinite(series_arr)):
            nan_indices = np.where(~np.isfinite(series_arr))[0].tolist()
            errors.append(f"Series '{name}' contains non-finite values (NaN/Inf) at indices: {nan_indices}")
            
        # Check for non-negative values
        if np.any(series_arr < 0):
            neg_indices = np.where(series_arr < 0)[0].tolist()
            errors.append(f"Series '{name}' contains negative values at indices: {neg_indices}")

    # Cross-series validation checks
    if not errors:
        for i in range(n):
            y = year[i]
            lam = caseload[i]
            kap = examined[i]
            det = detected[i]
            
            if kap > lam:
                errors.append(f"Period {y} (index {i}): examinations (examined={kap}) exceed caseload (caseload={lam}). This indicates a wrong construct mapping.")
            if det > kap:
                errors.append(f"Period {y} (index {i}): detected errors (detected={det}) exceed examinations (examined={kap}). This is mathematically impossible.")
                
    return errors
