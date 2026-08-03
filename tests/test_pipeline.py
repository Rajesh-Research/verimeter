import pytest
import os
import pandas as pd
import numpy as np

from validation.validator import validate_panel
from empirical.pipeline import run_pipeline

def test_pipeline_validator_consistent():
    # Healthy panel
    year = [2000 + i for i in range(10)]
    caseload = [1000 + 100*i for i in range(10)]
    examined = [500 + 50*i for i in range(10)]
    detected = [50 + 5*i for i in range(10)]
    
    errs = validate_panel(year, caseload, examined, detected)
    assert not errs, f"Expected no validation errors, got: {errs}"


def test_pipeline_validator_inconsistent():
    # Examined exceeds caseload
    year = [2000 + i for i in range(8)]
    caseload = [1000] * 8
    examined = [500] * 8
    examined[3] = 1200  # exceeds caseload
    detected = [50] * 8
    
    errs = validate_panel(year, caseload, examined, detected)
    assert len(errs) > 0
    assert "exceed caseload" in errs[0]


def test_pipeline_validator_detected_exceeds_examined():
    # Detected exceeds examined
    year = [2000 + i for i in range(8)]
    caseload = [1000] * 8
    examined = [500] * 8
    detected = [50] * 8
    detected[4] = 600  # exceeds examined
    
    errs = validate_panel(year, caseload, examined, detected)
    assert len(errs) > 0
    assert "exceed examinations" in errs[0]


def test_pipeline_validator_too_short():
    # Panel too short
    year = [2000, 2001, 2002]
    caseload = [1000, 1100, 1200]
    examined = [500, 550, 600]
    detected = [50, 55, 60]
    
    errs = validate_panel(year, caseload, examined, detected)
    assert len(errs) > 0
    assert "requires at least 8 periods" in errs[0]


def test_all_pipelines_run():
    from empirical.pipeline import run_all_pipelines
    
    results = run_all_pipelines()
    
    assert len(results) == 9
    for name, df in results.items():
        assert isinstance(df, pd.DataFrame)
        # Check that standard panel columns exist
        for col in ["year", "caseload", "examined", "detected"]:
            assert col in df.columns
        assert len(df) > 0
        # Check logical panel bounds: examined <= caseload, detected <= examined
        assert np.all(df["examined"] <= df["caseload"])
        assert np.all(df["detected"] <= df["examined"])


def test_pipeline_checksum_provenance():
    # Verify that a run logs to datasets/provenance.jsonl
    prov_file = os.path.join("datasets", "provenance.jsonl")
    if os.path.exists(prov_file):
        os.remove(prov_file)
        
    from empirical.pipeline import run_all_pipelines
    run_all_pipelines()
    
    assert os.path.exists(prov_file)
    with open(prov_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    assert len(lines) >= 9
    import json
    for line in lines:
        record = json.loads(line)
        assert "timestamp" in record
        assert "sha256" in record
        assert "processed_rows" in record

