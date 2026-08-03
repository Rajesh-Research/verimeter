import pytest
import numpy as np

from verimeter.stats.monte_carlo import (
    monte_carlo_validation,
    compute_elasticity_power
)

def test_monte_carlo_validation():
    # Run a small Monte Carlo study to verify outputs
    res = monte_carlo_validation(n_replicates=10, n_periods=15, beta_true=0.4, seed=42)
    assert "beta_mean" in res
    assert "q_mean" in res
    assert 0 <= res["beta_mean"] <= 1.0
    assert 0 <= res["q_mean"] <= 0.20
    assert res["beta_mse"] >= 0
    assert res["q_mse"] >= 0


def test_compute_elasticity_power():
    # Run a small power study to verify outputs
    res = compute_elasticity_power(n_periods=15, beta_null=1.0, beta_alt=0.2, n_replicates=10, seed=42)
    assert "power" in res
    assert 0 <= res["power"] <= 1.0
    assert res["n_periods"] == 15
    assert res["beta_null"] == 1.0
    assert res["beta_alt"] == 0.2
