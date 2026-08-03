import os
import json
import numpy as np
import pandas as pd

from verimeter.diagnostics import capacity_elasticity
from validation.bootstrap import bootstrap_se, jackknife_se

DATASETS = [
    "eoir", "uspto", "ptab", "fda", "eudsa", "clinvar", "pcaob", "hospital", "asrs"
]

def run_empirical_validation(processed_dir="datasets/processed", 
                             output_dir="results/validation", 
                             table_dir="paper/tables"):
    """
    Runs verimeter capacity diagnostics and bootstrapped standard errors 
    across all 9 empirical datasets.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(table_dir, exist_ok=True)
    
    results = []
    
    print("=== Running Multi-Dataset Empirical Validation ===")
    
    for name in DATASETS:
        csv_path = os.path.join(processed_dir, f"{name}_panel.csv")
        if not os.path.exists(csv_path):
            print(f"Skipping missing panel: {csv_path}")
            continue
            
        print(f"Analyzing {name} panel...")
        df = pd.read_csv(csv_path)
        
        # 1. Main diagnostics
        try:
            # We bypass require_cointegration to get t_adf regardless of cointegration status
            ela = capacity_elasticity(df["caseload"], df["examined"], require_cointegration=False)
            
            # Estimator function for bootstrapping
            def get_beta(sub_df):
                sub_ela = capacity_elasticity(sub_df["caseload"], sub_df["examined"], require_cointegration=False)
                return sub_ela.beta
                
            # 2. Bootstrapped & Jackknifed SE
            boot_se = bootstrap_se(df, get_beta, n_boot=100)
            jack_se = jackknife_se(df, get_beta)
            
            results.append({
                "dataset": name.upper(),
                "observations": int(ela.n),
                "beta": float(ela.beta),
                "hac_se": float(ela.se),
                "boot_se": float(boot_se),
                "jack_se": float(jack_se),
                "eg_t": float(ela.adf_resid_t),
                "cointegrated": bool(ela.cointegrated),
                "verdict": ela.verdict.split(":")[0] # get short verdict tag
            })
        except Exception as e:
            print(f"Failed to analyze {name}: {e}")
            
    # Save as JSON
    json_path = os.path.join(output_dir, "empirical_validation.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    # Save as CSV
    val_df = pd.DataFrame(results)
    val_df.to_csv(os.path.join(output_dir, "empirical_validation.csv"), index=False)
    
    # Save as LaTeX Table
    tex_path = os.path.join(table_dir, "empirical_validation.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(r"""\begin{tabular}{lcccccccl}
\hline
\textbf{Agency} & \textbf{Obs} & $\hat{\beta}$ & \textbf{HAC se} & \textbf{Boot se} & \textbf{Jack se} & \textbf{EG } $t$ & \textbf{Coint?} & \textbf{Verdict Status} \\
\hline
""")
        for r in results:
            coint_str = "Yes" if r["cointegrated"] else "No"
            f.write(f"{r['dataset']} & {r['observations']} & {r['beta']:.3f} & {r['hac_se']:.3f} & {r['boot_se']:.3f} & {r['jack_se']:.3f} & {r['eg_t']:.2f} & {coint_str} & {r['verdict']} \\\\\n")
        f.write(r"""\hline
\end{tabular}
""")
        
    print(f"Empirical validation report successfully exported to {output_dir} and {table_dir}")


if __name__ == "__main__":
    run_empirical_validation()
