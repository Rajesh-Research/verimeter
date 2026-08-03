import os
import subprocess
import re
import shutil
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s][verimeter.paper][%(levelname)s] - %(message)s")
logger = logging.getLogger("paper_compile")

def convert_latex_table_to_html(tex_content: str) -> str:
    """
    Parses a LaTeX table string and returns a clean, styled HTML table.
    """
    # Remove standard latex comments and headers
    content = re.sub(r'\\begin{tabular}{.*}', '', tex_content)
    content = content.replace(r'\end{tabular}', '')
    content = content.replace(r'\hline', '')
    content = content.replace(r'\toprule', '')
    content = content.replace(r'\midrule', '')
    content = content.replace(r'\bottomrule', '')
    
    rows = content.strip().split(r'\\')
    html_rows = []
    
    for i, row in enumerate(rows):
        if not row.strip():
            continue
        cols = row.split('&')
        tag = 'th' if i == 0 else 'td'
        html_cols = []
        for col in cols:
            val = col.strip()
            # Clean up latex math formatting
            val = val.replace('$', '').replace(r'\beta', '&beta;').replace(r'\kappa', '&kappa;').replace(r'\lambda', '&lambda;').replace(r'\hat', '')
            html_cols.append(f"<{tag} style='padding: 10px; border-bottom: 1px solid #27272a; text-align: left;'>{val}</{tag}>")
        html_rows.append(f"<tr>{''.join(html_cols)}</tr>")
        
    return f"<table style='width: 100%; border-collapse: collapse; margin: 20px 0; background: #18181b; border: 1px solid #27272a; border-radius: 8px;'>{''.join(html_rows)}</table>"

def build_html_paper():
    """
    Constructs a styled publication-ready HTML edition of the manuscript.
    """
    logger.info("LaTeX engine not found. Compiling fallback HTML manuscript...")
    
    tex_path = os.path.join("paper", "manuscript.tex")
    with open(tex_path, "r", encoding="utf-8") as f:
        tex = f.read()
        
    # Extract Title & Abstract
    title_match = re.search(r'\\title{(.*?)}', tex)
    title = title_match.group(1) if title_match else "VERIMETER Manuscript"
    
    abstract_match = re.search(r'\\begin{abstract}(.*?)\\end{abstract}', tex, re.DOTALL)
    abstract = abstract_match.group(1).strip() if abstract_match else ""
    
    # Process sections
    sections = re.findall(r'\\section{(.*?)}\n(.*?)(?=\\section|\\subsection|\\begin{table}|\\begin{figure}|\\end{document})', tex, re.DOTALL)
    
    # Inlined HTML builder
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #09090b; color: #f4f4f5; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
  h1 {{ font-size: 2.2rem; color: #ffffff; border-bottom: 2px solid #2563eb; padding-bottom: 10px; margin-bottom: 5px; }}
  .author {{ font-style: italic; color: #a1a1aa; margin-bottom: 30px; }}
  .abstract {{ background: #18181b; border-left: 4px solid #2563eb; padding: 20px; border-radius: 4px; margin-bottom: 40px; font-size: 0.95rem; }}
  h2 {{ color: #ffffff; margin-top: 30px; border-bottom: 1px solid #27272a; padding-bottom: 5px; }}
  p {{ margin-bottom: 20px; color: #e4e4e7; }}
  .equation {{ background: #18181b; padding: 15px; border-radius: 6px; font-family: monospace; text-align: center; margin: 20px 0; border: 1px solid #27272a; }}
  .figure {{ text-align: center; margin: 30px 0; background: #18181b; padding: 20px; border-radius: 8px; border: 1px solid #27272a; }}
  .figure img {{ max-width: 100%; height: auto; border-radius: 4px; }}
  .caption {{ font-size: 0.85rem; color: #a1a1aa; margin-top: 10px; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="author">Research Architect & Principal Research Engineer | Verification Standards Unit</div>
<div class="abstract"><strong>Abstract:</strong> {abstract}</div>
"""

    # Inline Sections & Equations
    for sec_title, sec_body in sections:
        html += f"<h2>{sec_title}</h2>"
        body = sec_body.strip()
        
        # Format inline equations
        body = re.sub(r'\\begin{equation}(.*?)\\end{equation}', r'<div class="equation">\1</div>', body, flags=re.DOTALL)
        # Clean paragraph breaks
        paragraphs = body.split("\n\n")
        for p in paragraphs:
            if p.strip():
                html += f"<p>{p.strip()}</p>"

    # Inline Tables manually
    tables_to_embed = [
        ("tables/eoir_panel.tex", "Table 1: The EOIR Panel Data"),
        ("tables/attenuation_sensitivity.tex", "Table 2: Capacity Elasticity and Attenuation Sensitivity"),
        ("tables/dependence_bounds.tex", "Table 3: Screen Dependence Bounds")
    ]
    
    html += "<h2>Data Tables</h2>"
    for relative_path, caption in tables_to_embed:
        full_table_path = os.path.join("paper", relative_path)
        if os.path.exists(full_table_path):
            with open(full_table_path, "r", encoding="utf-8") as f:
                table_tex = f.read()
            html += f"<h3>{caption}</h3>"
            html += convert_latex_table_to_html(table_tex)
            
    # Include Figures
    html += "<h2>Figures</h2>"
    figures_to_embed = [
        ("../figures/eoir_inversion.png", "Figure 1: EOIR Declining Coverage vs reported error rate improvement."),
        ("../figures/dependence_bias.png", "Figure 2: Capture-Recapture understatement under screen dependence.")
    ]
    for fig_path, caption in figures_to_embed:
        html += f"""<div class="figure">
          <img src="{fig_path}" alt="{caption}" />
          <div class="caption">{caption}</div>
        </div>"""

    html += "</body>\n</html>"
    
    out_html_path = os.path.join("paper", "manuscript.html")
    with open(out_html_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    logger.info(f"HTML manuscript compiled successfully to: {out_html_path}")

def compile_latex():
    """
    Compiles manuscript.tex using pdflatex if installed.
    """
    # Check if setup class has compilation replacement
    tex_path = os.path.join("paper", "manuscript.tex")
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace document class to default article to resolve setup class dependency issues
    if r"\documentclass[11pt,article]{setup}" in content:
        content = content.replace(r"\documentclass[11pt,article]{setup}", r"\documentclass[11pt]{article}")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    logger.info("Attempting LaTeX compilation...")
    try:
        # Run pdflatex (run twice to resolve labels and table inputs)
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "manuscript.tex"],
            cwd="paper",
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "manuscript.tex"],
            cwd="paper",
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("PDF manuscript compiled successfully to paper/manuscript.pdf")
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.warning(f"pdflatex compilation failed or not available on PATH: {e}")
        # Build HTML fallback
        build_html_paper()

if __name__ == "__main__":
    compile_latex()
