import pytest
import os
import shutil

from verimeter.backend.database import engine
from verimeter.backend.storage import storage_client
from verimeter.backend.cache import cache_manager

def test_database_pooling():
    # Verify pool settings
    if hasattr(engine, "pool"):
        pool = engine.pool
        assert pool is not None
        from verimeter.backend.config import settings
        if "postgresql" in settings.DATABASE_URL and pool.__class__.__name__ == "QueuePool":
             assert pool.size() >= 15


def test_cache_manager():
    # Test setting values
    key = "test_key_2026"
    data = {"status": "verified", "score": 0.985}
    
    assert cache_manager.set(key, data, expire_seconds=10)
    assert cache_manager.get(key) == data
    
    # Test delete
    assert cache_manager.delete(key)
    assert cache_manager.get(key) is None


def test_object_storage_local_fallback(tmp_path):
    # Create a mock file
    mock_file = tmp_path / "empirical_run.tex"
    mock_file.write_text("LaTeX table content")
    
    # Run storage upload
    dest_path = storage_client.upload_file(str(mock_file))
    
    # Check that file exists at destination
    assert os.path.exists(dest_path)
    assert dest_path.endswith("empirical_run.tex")
    
    # Verify contents match
    with open(dest_path, "r") as f:
         content = f.read()
    assert content == "LaTeX table content"
    
    # Clean up local storage test artifact
    if os.path.exists(dest_path):
        try:
            os.remove(dest_path)
        except:
            pass
