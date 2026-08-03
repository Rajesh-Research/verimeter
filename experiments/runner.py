import os
import sys
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import hydra
from omegaconf import DictConfig

# Ensure src/ and root are in the path so we can import verimeter and modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "src"))
sys.path.insert(0, project_root)

import verimeter as V
from verimeter.logging_setup import setup_logging
from simulation.run_simulations import (
    run_spurious_regression_test,
    run_chapman_se_test,
    run_dependence_bias_test
)
from empirical.pipeline import run_pipeline

logger = logging.getLogger("verimeter.experiments")


def generate_eoir_outputs(panel_df, output_dir, table_dir, require_cointegration):
    """
    Runs the verimeter diagnostics on the EOIR panel data and generates its tables and plots.
    """
    logger.info("Running verimeter diagnostics on the EOIR panel...")
    
    # Run verimeter diagnose
    rep = V.diagnose(
        caseload=panel_df["caseload"].values,
        examined=panel_df["examined"].values,
        detected=panel_df["detected"].values,
        require_cointegration=require_cointegration
    )
    
    # Log report to console
    logger.info(f"\n{rep}")
    
    # Save Report to file
    report_txt_path = os.path.join(output_dir, "eoir_diagnostic_report.txt")
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write(str(rep))
    logger.info(f"EOIR text report written to {report_txt_path}")
    
    # Generate Table 1: EOIR Panel LaTeX Table
    logger.info("Generating EOIR Panel LaTeX table...")
    table_path_1 = os.path.join(table_dir, "eoir_panel.tex")
    with open(table_path_1, "w", encoding="utf-8") as f:
        f.write(r"""\begin{tabular}{cccccc}
\hline
\textbf{FY} & \textbf{Caseload ($\lambda$)} & \textbf{Completions ($\kappa$)} & \textbf{Examined Share ($\kappa/\lambda$)} & \textbf{BIA Completed} & \textbf{Reported Rate} \\
\hline
""")
        for i in range(len(panel_df)):
            row = panel_df.iloc[i]
            y = int(row["year"])
            lam = row["caseload"]
            kap = row["examined"]
            det = row["detected"]
            f.write(f"{y} & {lam:,.0f} & {kap:,.0f} & {kap/lam:.4f} & {det:,.0f} & {det/lam:.6f} \\\\\n")
        f.write(r"""\hline
\end{tabular}
""")
        
    # Generate Table 2: Attenuation Sensitivity LaTeX Table
    logger.info("Generating Attenuation Sensitivity LaTeX table...")
    ab = V.attenuation_bound(rep.elasticity.beta, panel_df["caseload"].values, 0.05)
    table_path_2 = os.path.join(table_dir, "attenuation_sensitivity.tex")
    with open(table_path_2, "w", encoding="utf-8") as f:
        f.write(r"""\begin{tabular}{lc}
\hline
\textbf{Parameter/Metric} & \textbf{Value} \\
\hline
Estimated Capacity Elasticity ($\hat{\beta}$) & """ + f"{rep.elasticity.beta:.4f}" + r""" \\
Assumed Regressor Measurement Error SD ($\sigma_u$) & 0.0500 \\
Reliability Coefficient & """ + f"{ab['reliability']:.4f}" + r""" \\
\textbf{Corrected Capacity Elasticity ($\beta_{corrected}$)} & \textbf{""" + f"{ab['beta_corrected']:.4f}" + r"""} \\
Inflation Factor & """ + f"{ab['inflation']:.4f}" + r""" \\
\hline
\end{tabular}
""")

    # Generate plots
    logger.info("Generating EOIR diagnostic plots...")
    
    # Plot 1: Caseload and Completions over Time
    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    color = '#d9534f'
    ax1.set_xlabel('Fiscal Year')
    ax1.set_ylabel('Caseload (Pending + New Receipts)', color=color)
    line1 = ax1.plot(panel_df["year"], panel_df["caseload"], color=color, marker='o', label='Caseload ($\lambda$)')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    ax2 = ax1.twinx()
    color = '#337ab7'
    ax2.set_ylabel('Examinations (Completions)', color=color)
    line2 = ax2.plot(panel_df["year"], panel_df["examined"], color=color, marker='s', label='Completions ($\kappa$)')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    plt.title('EOIR Workload Growth vs Review Capacity')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "eoir_workload.png"), dpi=300)
    plt.savefig(os.path.join(output_dir, "eoir_workload.pdf"))
    plt.close()
    
    # Plot 2: Examined Share and Reported Error Rate
    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    color = '#f0ad4e'
    ax1.set_xlabel('Fiscal Year')
    ax1.set_ylabel('Examined Share ($\kappa/\lambda$)', color=color)
    line1 = ax1.plot(panel_df["year"], panel_df["examined"] / panel_df["caseload"], color=color, marker='o', label='Examined Share')
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()
    color = '#5cb85c'
    ax2.set_ylabel('Reported Error Rate ($D/\lambda$)', color=color)
    line2 = ax2.plot(panel_df["year"], panel_df["detected"] / panel_df["caseload"], color=color, marker='^', label='Reported Rate')
    ax2.tick_params(axis='y', labelcolor=color)
    
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right')
    plt.title('EOIR Declining Coverage vs Dashboard Error Improvement')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "eoir_inversion.png"), dpi=300)
    plt.savefig(os.path.join(output_dir, "eoir_inversion.pdf"))
    plt.close()

    logger.info("EOIR plots and tables successfully generated.")


@hydra.main(config_path="configs", config_name="config", version_base="1.3")
def main(cfg: DictConfig):
    # Set up logger level based on config
    log_level = logging.INFO
    if cfg.logger.level == "DEBUG":
        log_level = logging.DEBUG
    elif cfg.logger.level == "WARNING":
        log_level = logging.WARNING
    setup_logging(log_level)
    
    logger.info("=== Starting VERIMETER Experiment Runner ===")
    logger.info(f"Seed: {cfg.seed}")
    
    # Set random seeds for numpy
    np.random.seed(cfg.seed)
    
    # Create target directories
    output_dir = os.path.abspath(cfg.output_dir)
    table_dir = os.path.abspath(cfg.table_dir)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(table_dir, exist_ok=True)
    
    # Run simulations if requested
    if cfg.experiment.run_simulations:
        logger.info("Running synthetic simulation track...")
        
        # 1. Spurious regression test
        logger.info("Running spurious regression false-positive test...")
        rates = run_spurious_regression_test(n_runs=cfg.simulation_runs, seed=cfg.seed)
        logger.info(f"False-positive inversion rates:")
        logger.info(f"  Naive OLS Regression: {rates['naive']*100:.2f}%")
        logger.info(f"  Dickey-Fuller Gate:   {rates['df_gate']*100:.2f}%")
        logger.info(f"  Engle-Granger Gate:   {rates['eg_gate']*100:.2f}%")
        
        # Save Spurious Regression LaTeX Table
        with open(os.path.join(table_dir, "spurious_regression.tex"), "w", encoding="utf-8") as f:
            f.write(r"""\begin{tabular}{lc}
\hline
\textbf{Model Specification} & \textbf{False Inversion Rate on Independent Random Walks} \\
\hline
Original (Naive Regression) & """ + f"{rates['naive']*100:.1f}\\%" + r""" \\
DF Cointegration Gate & """ + f"{rates['df_gate']*100:.1f}\\%" + r""" \\
\textbf{Engle-Granger Cointegration Gate (Hardened)} & \textbf{""" + f"{rates['eg_gate']*100:.1f}\\%" + r"""} \\
\hline
\end{tabular}
""")
            
        # 2. Chapman standard error validation
        logger.info("Running Chapman Standard Error validation test...")
        chapman = run_chapman_se_test(n_runs=cfg.simulation_runs, seed=cfg.seed)
        logger.info("Chapman SE calibration:")
        logger.info(f"  Empirical SD of q_hat:    {chapman['empirical_sd']:.6f}")
        logger.info(f"  Chapman Conditional SE:   {chapman['chapman_conditional_se']:.6f}")
        logger.info(f"  Combined Total SE:        {chapman['combined_total_se']:.6f}")
        logger.info(f"  Conditional Understatement: {chapman['understatement_pct']:.1f}%")
        
        with open(os.path.join(table_dir, "chapman_se.tex"), "w", encoding="utf-8") as f:
            f.write(r"""\begin{tabular}{lc}
\hline
\textbf{Metric} & \textbf{Standard Error Value} \\
\hline
Empirical Standard Deviation of $\hat{q}$ & """ + f"{chapman['empirical_sd']:.5f}" + r""" \\
Chapman Standard Error (Conditional on $N$) & """ + f"{chapman['chapman_conditional_se']:.5f} (Understates by " + f"{chapman['understatement_pct']:.1f}\\%" + r""") \\
\textbf{Combined Total Standard Error (Hardened)} & \textbf{""" + f"{chapman['combined_total_se']:.5f}" + r"""} \\
\hline
\end{tabular}
""")
            
        # 3. Screen dependence test
        logger.info("Running Screen Dependence bias test...")
        dep_results = run_dependence_bias_test(seed=cfg.seed)
        logger.info("Capture-Recapture understatement under screen dependence:")
        for r, res in dep_results.items():
            logger.info(f"  rho={r:.1f}: Estimated q={res['estimated_q']:.4f} (understated by {res['understated_pct']:.1f}%)")
            
        with open(os.path.join(table_dir, "dependence_bounds.tex"), "w", encoding="utf-8") as f:
            f.write(r"""\begin{tabular}{cccc}
\hline
\textbf{Reviewer-Skill Correlation ($\rho$)} & \textbf{True $q$} & \textbf{Estimated $q$} & \textbf{Understatement} \\
\hline
""")
            for r, res in dep_results.items():
                f.write(f"{r:.1f} & 0.100 & {res['estimated_q']:.4f} & {res['understated_pct']:.1f}\\% \\\\\n")
            f.write(r"""\hline
\end{tabular}
""")

        # Generate simulation plots
        fig, ax = plt.subplots(figsize=(6, 4))
        methods = ['Naive OLS', 'DF Gate', 'Engle-Granger']
        bar_rates = [rates['naive']*100, rates['df_gate']*100, rates['eg_gate']*100]
        bars = ax.bar(methods, bar_rates, color=['#d9534f', '#f0ad4e', '#5cb85c'])
        ax.set_ylabel('False Positive Inversion Rate (%)')
        ax.set_title('False Positives on Independent Random Walks')
        ax.set_ylim(0, 100)
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "spurious_regression.png"), dpi=300)
        plt.savefig(os.path.join(output_dir, "spurious_regression.pdf"))
        plt.close()
        
        fig, ax = plt.subplots(figsize=(6, 4))
        rhos = list(dep_results.keys())
        understatements = [dep_results[r]['understated_pct'] for r in rhos]
        ax.plot(rhos, understatements, marker='o', color='#337ab7', linewidth=2)
        ax.set_xlabel('Reviewer Skill Correlation ($\\rho$)')
        ax.set_ylabel('Understatement of Error Rate (%)')
        ax.set_title('Capture-Recapture Understatement under Screen Dependence')
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "dependence_bias.png"), dpi=300)
        plt.savefig(os.path.join(output_dir, "dependence_bias.pdf"))
        plt.close()
        
        logger.info("Simulation plots and tables successfully generated.")

    # Run empirical pipeline if requested
    if cfg.experiment.run_empirical:
        logger.info("Running empirical workload track...")
        try:
            panel_df = run_pipeline()
            generate_eoir_outputs(panel_df, output_dir, table_dir, cfg.require_cointegration)
        except Exception as e:
            logger.error(f"Failed to run empirical pipeline: {e}")
            sys.exit(1)
            
    logger.info("=== VERIMETER Experiment Runner Finished ===")


if __name__ == "__main__":
    main()
