import pytest
import numpy as np

import verimeter as V

def test_examined_share_census():
    caseload = [1000, 1200, 1500]
    examined = [500, 600, 750]
    
    es = V.examined_share(caseload, examined, kappa_is_sample=False)
    assert es.is_census
    assert np.allclose(es.share, [0.5, 0.5, 0.5])
    assert es.ci_low is None
    assert es.ci_high is None
    
    summary = es.summary()
    assert "census: no sampling interval applies" in summary
    assert "mean 0.5000" in summary


def test_examined_share_sample():
    caseload = [100, 200]
    examined = [50, 80]
    
    es = V.examined_share(caseload, examined, kappa_is_sample=True, alpha=0.05)
    assert not es.is_census
    assert es.ci_low is not None
    assert es.ci_high is not None
    assert len(es.ci_low) == 2
    assert np.all(es.ci_low >= 0)
    assert np.all(es.ci_high <= 1)


def test_examined_share_exceptions():
    with pytest.raises(ValueError):
        V.examined_share([100, 100], [50])  # mismatched length
        
    with pytest.raises(ValueError):
        V.examined_share([100, 100], [120, 50])  # examined > caseload
        
    with pytest.raises(ValueError):
        V.examined_share([100, np.nan], [50, 50])  # NaN input
        
    with pytest.raises(ValueError):
        V.examined_share([100, 0], [50, 0])  # non-positive caseload


def test_capacity_elasticity_exceptions():
    # Length < 8
    with pytest.raises(ValueError, match="need at least 8 periods"):
        V.capacity_elasticity([100]*5, [50]*5)
        
    # No caseload variation
    with pytest.raises(ValueError, match="no variation"):
        V.capacity_elasticity([100]*10, [50]*10)


def test_two_screen():
    # Normal case
    n11, n10, n01 = 20, 30, 40
    n_overlap = 1000
    
    est = V.two_screen(n11, n10, n01, n_overlap, alpha=0.05)
    assert est.n_overlap == n_overlap
    assert est.delta1 == pytest.approx(20 / 60)  # n11 / n_1 where n_1 = n11 + n01 = 60
    assert est.delta2 == pytest.approx(20 / 50)  # n11 / n1_ where n1_ = n11 + n10 = 50
    assert est.q > 0
    assert len(est.q_ci) == 2
    assert est.se_conditional > 0
    assert est.se_total > est.se_conditional / n_overlap


def test_two_screen_exceptions():
    with pytest.raises(ValueError):
        V.two_screen(-1, 10, 10, 100)  # negative counts
        
    with pytest.raises(ValueError):
        V.two_screen(5, 5, 5, 10)  # detected > overlap (5+5+5 = 15 > 10)
        
    with pytest.raises(ValueError):
        V.two_screen(0, 10, 10, 100)  # n11 = 0


def test_three_screen():
    counts = {
        '111': 10,
        '110': 20,
        '101': 15,
        '011': 25,
        '100': 30,
        '010': 40,
        '001': 35
    }
    n_overlap = 5000
    res = V.three_screen(counts, n_overlap)
    assert res["converged"]
    assert res["N_true"] > sum(counts.values())
    assert len(res["delta"]) == 3
    assert res["df"] == 3


def test_overlap_required():
    req = V.overlap_required(delta_from=0.6, delta_to=0.5, q=0.08, power=0.8, alpha=0.05)
    assert req["caught_error_pairs"] > 0
    assert req["overlap_cases"] > 0
    assert "q = 0.08" in req["note"]
