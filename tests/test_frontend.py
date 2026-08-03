import pytest
import os
import json

def test_frontend_project_structure():
    frontend_dir = "frontend"
    assert os.path.exists(frontend_dir)
    assert os.path.exists(os.path.join(frontend_dir, "package.json"))
    assert os.path.exists(os.path.join(frontend_dir, "src", "app", "page.tsx"))
    assert os.path.exists(os.path.join(frontend_dir, "src", "app", "globals.css"))

def test_frontend_dependencies():
    with open("frontend/package.json", "r") as f:
        pkg = json.load(f)
    
    deps = pkg.get("dependencies", {})
    assert "next" in deps
    assert "react" in deps
    assert "recharts" in deps
    assert "framer-motion" in deps
    assert "lucide-react" in deps
