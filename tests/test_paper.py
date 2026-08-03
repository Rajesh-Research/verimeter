import pytest
import os
import shutil

from paper.compile import build_html_paper, compile_latex

def test_manuscript_source_exists():
    assert os.path.exists("paper/manuscript.tex")
    assert os.path.isdir("paper/tables")

def test_manuscript_html_compilation():
    # If the file already exists, remove it to verify regeneration
    html_path = "paper/manuscript.html"
    if os.path.exists(html_path):
        os.remove(html_path)
        
    build_html_paper()
    assert os.path.exists(html_path)
    
    # Read and verify content contains title and abstract structure
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    assert "The Denominator That Isn't There" in html
    assert "Abstract:" in html
    assert "Table 1:" in html
