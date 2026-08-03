import pytest
import os
import shutil
import numpy as np

from simulation.institution import InstitutionPanel
from simulation.policy import CapacityBooster, QualityTraining
from simulation.engine import SimulationEngine

def test_institution_panel_init():
    panel = InstitutionPanel(n_institutions=50, n_periods=10, seed=42)
    assert panel.caseload.shape == (50, 10)
    assert panel.staff.shape == (50, 10)
    assert np.all(panel.caseload[:, 0] > 0)
    assert np.all(panel.staff[:, 0] > 0)
    assert np.all(panel.true_error_rate[:, 0] > 0)


def test_institution_panel_steps():
    panel = InstitutionPanel(n_institutions=20, n_periods=5, seed=42)
    panel.step_demographics(t=1, growth_lambda=0.04, growth_staff=0.02)
    
    # Caseload and staff at t=1 should be different from t=0
    assert np.any(panel.caseload[:, 1] != panel.caseload[:, 0])
    assert np.all(panel.staff[:, 1] == panel.staff[:, 0] * 1.02)
    
    panel.calculate_capacity_and_reviews(t=1)
    assert np.all(panel.examined[:, 1] <= panel.caseload[:, 1])
    assert np.all(panel.examined[:, 1] <= panel.capacity[:, 1])


def test_policy_interventions():
    panel = InstitutionPanel(n_institutions=20, n_periods=5, seed=42)
    
    booster = CapacityBooster(start_period=2, hiring_increase_pct=0.5)
    training = QualityTraining(start_period=3, quality_improvement_pct=0.2)
    
    # Period 1 (no changes)
    panel.step_demographics(t=1)
    booster.apply(panel, t=1)
    training.apply(panel, t=1)
    assert panel.staff[0, 1] == panel.staff[0, 0] # no booster yet
    
    # Period 2 (booster triggers)
    panel.step_demographics(t=2)
    booster.apply(panel, t=2)
    training.apply(panel, t=2)
    assert panel.staff[0, 2] == pytest.approx(panel.staff[0, 1] * 1.5)
    assert panel.true_error_rate[0, 2] == panel.true_error_rate[0, 1] # no training yet
    
    # Period 3 (training triggers)
    panel.step_demographics(t=3)
    booster.apply(panel, t=3)
    training.apply(panel, t=3)
    assert panel.true_error_rate[0, 3] == pytest.approx(panel.true_error_rate[0, 2] * 0.8)


def test_simulation_engine_run_and_export(tmp_path):
    engine = SimulationEngine(n_institutions=10, n_periods=5, seed=42)
    engine.add_policy(CapacityBooster(start_period=2, hiring_increase_pct=0.3))
    engine.run(growth_lambda=0.05, growth_staff=0.01)
    
    df = engine.get_summary_df()
    assert len(df) == 5
    assert list(df.columns) == ["year", "caseload", "examined", "true_error_rate", "n11", "n10", "n01", "n_overlap"]
    
    # Test exports using temp dir path
    out_dir = str(tmp_path / "results")
    fig_dir = str(tmp_path / "figures")
    tbl_dir = str(tmp_path / "tables")
    
    engine.export_data(out_dir, "sim_test")
    engine.export_latex_table(tbl_dir, "sim_test")
    engine.export_plots(fig_dir, "sim_test")
    
    assert os.path.exists(os.path.join(out_dir, "sim_test.csv"))
    assert os.path.exists(os.path.join(out_dir, "sim_test.json"))
    assert os.path.exists(os.path.join(tbl_dir, "sim_test.tex"))
    assert os.path.exists(os.path.join(fig_dir, "sim_test.png"))
    assert os.path.exists(os.path.join(fig_dir, "sim_test.pdf"))
    assert os.path.exists(os.path.join(fig_dir, "sim_test.svg"))
