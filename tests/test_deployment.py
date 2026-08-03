import pytest
import os
import yaml

def test_deployment_files_exist():
    assert os.path.exists("Dockerfile")
    assert os.path.exists("frontend/Dockerfile")
    assert os.path.exists("docker-compose.yml")
    assert os.path.exists(".github/workflows/ci.yml")
    assert os.path.exists("scripts/deploy.ps1")

def test_github_actions_yaml_syntax():
    workflow_path = ".github/workflows/ci.yml"
    with open(workflow_path, "r") as f:
         try:
             data = yaml.safe_load(f)
             assert data is not None
             assert "name" in data
             assert "jobs" in data
             assert "test" in data["jobs"]
         except yaml.YAMLError as exc:
             pytest.fail(f"YAML parsing error on GHA workflow: {exc}")
