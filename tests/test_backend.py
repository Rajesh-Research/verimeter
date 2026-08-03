import pytest
from fastapi.testclient import TestClient
import os
import shutil

from verimeter.backend.app import app
from verimeter.backend.database import SessionLocal, Base, engine

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Setup fresh sqlite db for testing
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup database file after tests
    if os.path.exists("./verimeter.db"):
         try:
              os.remove("./verimeter.db")
         except:
              pass


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "verimeter-backend"


def test_auth_flow():
    # 1. Register a test user
    reg_payload = {
        "email": "researcher@justice.gov",
        "password": "super_secret_password_123"
    }
    response = client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 200
    assert response.json()["email"] == "researcher@justice.gov"
    assert "id" in response.json()
    
    # 2. Login with credentials
    login_data = {
        "username": "researcher@justice.gov",
        "password": "super_secret_password_123"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    token = response.json()["access_token"]
    
    # 3. Retrieve me profile
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "researcher@justice.gov"


def test_datasets_endpoints():
    # Login to get token
    login_data = {
        "username": "researcher@justice.gov",
        "password": "super_secret_password_123"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # List datasets
    response = client.get("/api/v1/datasets/list", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_experiments_endpoints():
    # Login to get token
    login_data = {
        "username": "researcher@justice.gov",
        "password": "super_secret_password_123"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Run experiment on pre-processed EOIR panel
    payload = {
        "dataset_name": "eoir",
        "require_cointegration": False
    }
    response = client.post("/api/v1/experiments/run", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_name"] == "eoir"
    assert "beta" in data
    assert "verdict" in data
    
    # Export LaTeX table
    result_id = data["id"]
    response = client.get(f"/api/v1/experiments/exports/{result_id}/table", headers=headers)
    assert response.status_code == 200
    assert "tabular" in response.text
