import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from simulation.institution import InstitutionPanel
from simulation.policy import PolicyIntervention

class SimulationEngine:
    """
    Orchestrates the institution panel simulation and manages multi-format data exports.
    """
    def __init__(self, n_institutions: int, n_periods: int, seed: int = 42):
        self.panel = InstitutionPanel(n_institutions, n_periods, seed)
        self.policies = []

    def add_policy(self, policy: PolicyIntervention):
        self.policies.append(policy)

    def run(self, growth_lambda: float = 0.06, growth_staff: float = 0.01,
            selection_bias_alpha: float = 1.0, measurement_error_sd: float = 0.0):
        """
        Executes the simulation loop across all periods.
        """
        for t in range(1, self.panel.n_periods):
            # 1. Update demographics (caseload growth)
            self.panel.step_demographics(t, growth_lambda, growth_staff)
            
            # 2. Apply active policy interventions (e.g. staff hiring boosts)
            for policy in self.policies:
                policy.apply(self.panel, t)
                
            # If no training policy, propagate previous error rates
            if not any(hasattr(p, 'quality_improvement_pct') for p in self.policies):
                self.panel.true_error_rate[:, t] = self.panel.true_error_rate[:, t-1]
                
            # 3. Calculate capacity constraints and completions
            self.panel.calculate_capacity_and_reviews(t, selection_bias_alpha)
            
        # Add measurement error to caseload if specified
        if measurement_error_sd > 0:
            noise = np.random.normal(0, measurement_error_sd, self.panel.caseload.shape)
            self.panel.caseload = self.panel.caseload * np.exp(noise)

    def get_summary_df(self) -> pd.DataFrame:
        """
        Aggregates individual institution metrics to a single annual timeseries.
        """
        years = np.arange(2016, 2016 + self.panel.n_periods)
        mean_caseload = self.panel.caseload.mean(axis=0)
        mean_examined = self.panel.examined.mean(axis=0)
        mean_true_errors = (self.panel.caseload * self.panel.true_error_rate).mean(axis=0)
        
        # Simulated double screen counts (for capture recapture)
        # Assume screen1 delta = 0.60, screen2 delta = 0.45
        n_overlap = 4000
        q = self.panel.true_error_rate.mean(axis=0)
        n_true = (n_overlap * q).astype(int)
        
        n11 = np.random.binomial(n_true, 0.60 * 0.45)
        n10 = np.random.binomial(n_true, 0.60 * (1 - 0.45))
        n01 = np.random.binomial(n_true, (1 - 0.60) * 0.45)
        
        # Map examined share
        df = pd.DataFrame({
            "year": years,
            "caseload": mean_caseload,
            "examined": mean_examined,
            "true_error_rate": q,
            "n11": n11,
            "n10": n10,
            "n01": n01,
            "n_overlap": n_overlap
        })
        return df

    def export_data(self, output_dir: str, base_filename: str):
        """
        Exports summary metrics to CSV and JSON formats.
        """
        os.makedirs(output_dir, exist_ok=True)
        df = self.get_summary_df()
        
        # 1. Export CSV
        csv_path = os.path.join(output_dir, f"{base_filename}.csv")
        df.to_csv(csv_path, index=False)
        
        # 2. Export JSON
        json_path = os.path.join(output_dir, f"{base_filename}.json")
        data = df.to_dict(orient="records")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def export_latex_table(self, table_dir: str, base_filename: str):
        """
        Exports summary metrics to LaTeX table format.
        """
        os.makedirs(table_dir, exist_ok=True)
        df = self.get_summary_df()
        
        tex_path = os.path.join(table_dir, f"{base_filename}.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(r"""\begin{tabular}{ccccc}
\hline
\textbf{Year} & \textbf{Average Caseload} & \textbf{Average Examined} & \textbf{True Error Rate} & \textbf{Overlap Cases} \\
\hline
""")
            for idx, row in df.iterrows():
                f.write(f"{int(row['year'])} & {row['caseload']:.1f} & {row['examined']:.1f} & {row['true_error_rate']:.4f} & {int(row['n_overlap'])} \\\\\n")
            f.write(r"""\hline
\end{tabular}
""")

    def export_plots(self, figure_dir: str, base_filename: str):
        """
        Exports capacity and error graphs as PNG, PDF, and SVG formats.
        """
        os.makedirs(figure_dir, exist_ok=True)
        df = self.get_summary_df()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Capacity scaling plot
        ax1.plot(df["year"], df["caseload"], label="Caseload", color="#1f77b4", marker="o")
        ax1.plot(df["year"], df["examined"], label="Completions", color="#ff7f0e", marker="s")
        ax1.set_xlabel("Year")
        ax1.set_ylabel("Volume")
        ax1.set_title("Caseload vs Capacity Scale")
        ax1.grid(True, linestyle="--", alpha=0.5)
        ax1.legend()
        
        # True error rate plot
        ax2.plot(df["year"], df["true_error_rate"] * 100.0, label="True Quality (Error %)", color="#d62728", marker="^")
        ax2.set_xlabel("Year")
        ax2.set_ylabel("Rate (%)")
        ax2.set_title("True Quality Profile")
        ax2.grid(True, linestyle="--", alpha=0.5)
        ax2.legend()
        
        plt.tight_layout()
        
        # Save to requested formats
        for ext in ["png", "pdf", "svg"]:
            plt.savefig(os.path.join(figure_dir, f"{base_filename}.{ext}"), dpi=300)
        plt.close()
