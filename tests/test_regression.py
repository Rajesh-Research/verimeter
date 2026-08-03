import pytest
import numpy as np

from verimeter.stats.regression import (
    fit_ols,
    compute_hac_se,
    compute_outlier_diagnostics,
    correct_measurement_error
)

def test_fit_ols():
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 5, 4, 5]
    res = fit_ols(x, y)
    assert res["slope"] == pytest.approx(0.6)
    assert res["intercept"] == pytest.approx(2.2)
    assert len(res["residuals"]) == 5
    assert np.allclose(res["residuals"], np.array(y) - (2.2 + 0.6 * np.array(x)))


def test_compute_hac_se():
    x = np.arange(10, dtype=float)
    resid = np.random.normal(0, 1, 10)
    se = compute_hac_se(x, resid, nlags=1)
    assert np.isfinite(se)
    assert se > 0


def test_compute_outlier_diagnostics():
    x = [1, 2, 3, 4, 10]  # 10 is an outlier
    y = [2, 4, 5, 4, 25]  # 25 is also an outlier
    diag = compute_outlier_diagnostics(x, y)
    
    assert len(diag["cooks_d"]) == 5
    assert len(diag["dfbetas"]) == 5
    assert len(diag["leverage"]) == 5
    
    # The last element should have high Cook's D and leverage
    assert diag["cooks_d"][4] > diag["cooks_d"][0]
    assert diag["leverage"][4] > diag["leverage"][0]


def test_correct_measurement_error():
    x = [1, 2, 3, 4, 5]
    res = correct_measurement_error(0.6, x, 0.1, 0.5)
    assert res["reliability"] == pytest.approx(1 - 0.25 / 2.5) # var_x of 1..5 is 2.5
    assert res["beta_corrected"] == pytest.approx(0.6 / res["reliability"])
    assert res["se_corrected"] == pytest.approx(0.1 / res["reliability"])
    assert "caseload" in res["note"]
