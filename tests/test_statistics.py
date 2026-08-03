import numpy as np

import verimeter as V
from simulation.data_generator import generate_panel_data, generate_capture_recapture_data

def test_spurious_regression_gate():
    """
    Verifies that the Engle-Granger cointegration gate correctly identifies independent random walks
    as unreliable, rather than confirming capacity inversion.
    """
    np.random.seed(42)
    # Generate two independent random walks
    n_periods = 35
    log_lam = np.cumsum(np.random.normal(0.05, 0.1, n_periods))
    log_kap = np.cumsum(np.random.normal(0.05, 0.1, n_periods))
    
    lam = np.exp(log_lam) * 1000.0
    kap = np.exp(log_kap) * 500.0
    
    # Run verimeter diagnostics
    ela = V.capacity_elasticity(lam, kap, require_cointegration=True)
    
    # Since they are independent, cointegration should fail
    # and it should mark the result as unreliable
    if not ela.cointegrated:
        assert not ela.reliable
        assert "SPURIOUS" in ela.verdict or "UNDERPOWERED" in ela.verdict
    else:
        # Statistically it might cointegrate occasionally (size ~3.8%), which is fine,
        # but for this specific seed (42) it should fail cointegration
        assert not ela.reliable
        assert "SPURIOUS" in ela.verdict


def test_chapman_se_calibration():
    """
    Verifies that the total SE is strictly greater than the conditional Chapman SE
    due to incorporating the binomial variation component.
    """
    n_overlap = 3000
    # Independent screens
    data = generate_capture_recapture_data(
        n_overlap=n_overlap, q_true=0.10, delta1=0.60, delta2=0.40, rho=0.0, seed=123
    )
    
    est = V.two_screen(data["n11"], data["n10"], data["n01"], n_overlap)
    
    # Check that total SE includes the binomial component
    # total_se = sqrt(var_cond + var_binom)
    # conditional_se is of N, so to compare, we convert to rate:
    se_cond_rate = est.se_conditional / n_overlap
    
    assert est.se_total > se_cond_rate
    # Chapman SE ratio should be around 1.02 to 1.30 of conditional
    assert est.se_total / se_cond_rate > 1.05
