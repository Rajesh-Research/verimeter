import pytest
import os
import pandas as pd
import numpy as np

from validation.bootstrap import bootstrap_se, jackknife_se
from validation.run_validation import run_empirical_validation

def test_bootstrap_and_jackknife_se():
    # Construct a simple panel DataFrame
    np.random.seed(42)
    t = 15
    df = pd.DataFrame({
        "caseload": np.exp(np.linspace(6.0, 7.5, t) + np.random.normal(0, 0.05, t)),
        "examined": np.exp(np.linspace(4.5, 5.5, t) + np.random.normal(0, 0.05, t))
    })
    
    # Estimator function
    from verimeter.diagnostics import capacity_elasticity
    def get_beta(sub_df):
        ela = capacity_elasticity(sub_df["caseload"], sub_df["examined"], require_cointegration=False)
        return ela.beta
        
    boot = bootstrap_se(df, get_beta, n_boot=20, seed=42)
    jack = jackknife_se(df, get_beta)
    
    assert np.isfinite(boot)
    assert np.isfinite(jack)
    assert boot > 0
    assert jack > 0


def test_empirical_validation_runner(tmp_path):
    # Test that run_empirical_validation runs without errors on a subset of datasets
    out_dir = str(tmp_path / "results")
    tbl_dir = str(tmp_path / "tables")
    
    # We run it using our already processed panels in datasets/processed
    run_empirical_validation(processed_dir="datasets/processed", 
                             output_dir=out_dir, 
                             table_dir=tbl_dir)
                             
    # Check that output files were successfully created
    assert os.path.exists(os.path.join(out_dir, "empirical_validation.json"))
    assert os.path.exists(os.path.join(out_dir, "empirical_validation.csv"))
    assert os.path.exists(os.path.join(tbl_dir, "empirical_validation.tex"))
