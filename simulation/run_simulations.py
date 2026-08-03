import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from simulation.data_generator import generate_panel_data, generate_capture_recapture_data
from verimeter.diagnostics import capacity_elasticity, two_screen

def run_spurious_regression_test(n_runs=100, n_periods=40, seed=42):
    """
    Simulates independent random walks to test the false positive rate of 
    identifying 'capacity inversion' under naive regression, DF gate, and EG gate.
    """
    np.random.seed(seed)
    
    naive_inversion_count = 0
    df_gate_inversion_count = 0
    eg_gate_inversion_count = 0
    
    # Dickey-Fuller 5% critical value for n=40 is approx -2.93 (with intercept)
    df_critical_val = -2.93
    # Engle-Granger 5% critical value for n=40 is approx -3.49
    
    for i in range(n_runs):
        # Generate independent random walks
        # caseload lam and examined kap are completely independent
        log_lam = np.cumsum(np.random.normal(0.05, 0.1, n_periods))
        log_kap = np.cumsum(np.random.normal(0.05, 0.1, n_periods))
        
        lam = np.exp(log_lam) * 1000.0
        kap = np.exp(log_kap) * 500.0
        
        # Naive regression: log(kap) = alpha + beta * log(lam)
        res = stats.linregress(log_lam, log_kap)
        beta_hat = res.slope
        se = res.stderr if res.stderr > 0 else 1e-9
        
        # Test H0: beta = 1
        t_stat = (beta_hat - 1) / se
        p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n_periods - 2))
        
        is_naive_inversion = (p_val < 0.05) and (beta_hat < 1)
        if is_naive_inversion:
            naive_inversion_count += 1
            
        # Cointegration residual t-statistic calculation
        resid = log_kap - (res.intercept + beta_hat * log_lam)
        dx = np.diff(resid)
        # 1-lag Dickey-Fuller on residuals
        n_dx = len(dx)
        X = np.column_stack([resid[:n_dx], np.ones(n_dx)])
        try:
            b, *_ = np.linalg.lstsq(X, dx, rcond=None)
            r = dx - X @ b
            dof = n_dx - 2
            s2 = float(r @ r) / dof
            XtX = np.linalg.pinv(X.T @ X)
            se_b = float(np.sqrt(s2 * XtX[0, 0]))
            t_adf = b[0] / se_b if se_b > 0 else 0.0
        except:
            t_adf = 0.0
            
        # DF gate: cointegrated if t_adf < df_critical_val
        is_df_coint = t_adf < df_critical_val
        if is_df_coint and is_naive_inversion:
            df_gate_inversion_count += 1
            
        # EG gate: cointegrated if t_adf < -3.49 (calculated dynamically in verimeter)
        # Using verimeter diagnostics:
        try:
            ela = capacity_elasticity(lam, kap, require_cointegration=True)
            if ela.reliable and "INVERSION CONFIRMED" in ela.verdict:
                eg_gate_inversion_count += 1
        except:
            pass
            
    rates = {
        "naive": naive_inversion_count / n_runs,
        "df_gate": df_gate_inversion_count / n_runs,
        "eg_gate": eg_gate_inversion_count / n_runs
    }
    return rates


def run_chapman_se_test(n_runs=500, n_overlap=4000, q_true=0.10, delta1=0.55, delta2=0.40, seed=42):
    """
    Validates that the combined Chapman standard error (conditional + binomial) matches 
    the true empirical standard deviation of the true error rate estimator.
    """
    estimates = []
    se_conds = []
    se_tots = []
    
    for i in range(n_runs):
        data = generate_capture_recapture_data(
            n_overlap=n_overlap, q_true=q_true, delta1=delta1, delta2=delta2, rho=0.0, seed=seed+i
        )
        try:
            est = two_screen(data["n11"], data["n10"], data["n01"], n_overlap)
            estimates.append(est.q)
            se_conds.append(est.se_conditional / n_overlap)
            se_tots.append(est.se_total / n_overlap)
        except Exception:
            pass
            
    emp_sd = np.std(estimates)
    mean_se_cond = np.mean(se_conds)
    mean_se_tot = np.mean(se_tots)
    
    return {
        "empirical_sd": emp_sd,
        "chapman_conditional_se": mean_se_cond,
        "combined_total_se": mean_se_tot,
        "understatement_pct": 100 * (1 - mean_se_cond / emp_sd)
    }


def run_dependence_bias_test(n_overlap=4000, q_true=0.10, delta1=0.55, delta2=0.40, seed=42):
    """
    Evaluates the bias of two-screen capture-recapture under various levels of screen dependence.
    """
    rhos = [0.0, 0.3, 0.6, 0.9]
    results = {}
    
    for r in rhos:
        # Run multiple trials to get a stable estimate
        trial_qs = []
        for trial in range(50):
            data = generate_capture_recapture_data(
                n_overlap=n_overlap, q_true=q_true, delta1=delta1, delta2=delta2, rho=r, seed=seed+trial
            )
            try:
                est = two_screen(data["n11"], data["n10"], data["n01"], n_overlap)
                trial_qs.append(est.q)
            except:
                pass
        mean_q = np.mean(trial_qs)
        results[r] = {
            "estimated_q": mean_q,
            "understated_pct": 100 * (1 - mean_q / q_true)
        }
    return results


def generate_plots_and_tables(output_dir="figures", table_dir="paper/tables"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(table_dir, exist_ok=True)
    
    print("Running Spurious Regression tests...")
    spurious_rates = run_spurious_regression_test(n_runs=150)
    print(f"Spurious Rates: {spurious_rates}")
    
    # Save Spurious Regression LaTeX Table
    with open(os.path.join(table_dir, "spurious_regression.tex"), "w") as f:
        f.write(r"""\begin{tabular}{lc}
\hline
\textbf{Model Specification} & \textbf{False Inversion Rate on Independent Random Walks} \\
\hline
Original (Naive Regression) & """ + f"{spurious_rates['naive']*100:.1f}\\%" + r""" \\
DF Cointegration Gate & """ + f"{spurious_rates['df_gate']*100:.1f}\\%" + r""" \\
\textbf{Engle-Granger Cointegration Gate (Hardened)} & \textbf{""" + f"{spurious_rates['eg_gate']*100:.1f}\\%" + r"""} \\
\hline
\end{tabular}
""")
        
    print("Running Chapman SE validation...")
    chapman_results = run_chapman_se_test(n_runs=150)
    print(f"Chapman validation: {chapman_results}")
    
    with open(os.path.join(table_dir, "chapman_se.tex"), "w") as f:
        f.write(r"""\begin{tabular}{lc}
\hline
\textbf{Metric} & \textbf{Standard Error Value} \\
\hline
Empirical Standard Deviation of $\hat{q}$ & """ + f"{chapman_results['empirical_sd']:.5f}" + r""" \\
Chapman Standard Error (Conditional on $N$) & """ + f"{chapman_results['chapman_conditional_se']:.5f}" + r""" (Understates by """ + f"{chapman_results['understatement_pct']:.1f}\\%" + r""") \\
\textbf{Combined Total Standard Error (Hardened)} & \textbf{""" + f"{chapman_results['combined_total_se']:.5f}" + r"""} \\
\hline
\end{tabular}
""")

    print("Running Screen Dependence tests...")
    dep_results = run_dependence_bias_test()
    print(f"Dependence Results: {dep_results}")
    
    with open(os.path.join(table_dir, "dependence_bounds.tex"), "w") as f:
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

    # Make plots
    # 1. Spurious regression bar chart
    fig, ax = plt.subplots(figsize=(6, 4))
    methods = ['Naive OLS', 'DF Gate', 'Engle-Granger']
    rates = [spurious_rates['naive']*100, spurious_rates['df_gate']*100, spurious_rates['eg_gate']*100]
    bars = ax.bar(methods, rates, color=['#d9534f', '#f0ad4e', '#5cb85c'])
    ax.set_ylabel('False Positive Inversion Rate (%)')
    ax.set_title('False Positives on Independent Random Walks')
    ax.set_ylim(0, 100)
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "spurious_regression.png"), dpi=300)
    plt.savefig(os.path.join(output_dir, "spurious_regression.pdf"))
    plt.close()
    
    # 2. Dependence bias line plot
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
    
    print("Simulations and auto-generations complete.")


def run_scalable_simulation(output_dir="results/simulation", figure_dir="figures", table_dir="paper/tables"):
    """
    Executes a large-scale institutional simulation using the Phase 4 Simulation Engine.
    """
    from simulation.engine import SimulationEngine
    from simulation.policy import CapacityBooster, QualityTraining
    
    print("Running scalable SimulationEngine run...")
    # Simulate 1000 institutions across 12 periods
    engine = SimulationEngine(n_institutions=1000, n_periods=12, seed=42)
    
    # Add a capacity boost intervention starting at period 6 (e.g. year 2022)
    engine.add_policy(CapacityBooster(start_period=6, hiring_increase_pct=0.4))
    
    # Add quality training starting at period 8 (e.g. year 2024)
    engine.add_policy(QualityTraining(start_period=8, quality_improvement_pct=0.25))
    
    engine.run(growth_lambda=0.05, growth_staff=0.01)
    
    # Export all requested formats
    engine.export_data(output_dir, "simulation_panel")
    engine.export_latex_table(table_dir, "simulation_summary")
    engine.export_plots(figure_dir, "simulation_plots")
    
    # Extra verification exports
    engine.export_plots(output_dir, "simulation_plots") # also save vector copies in results
    print("Scalable simulation complete. Outputs generated in CSV, JSON, LaTeX, PNG, PDF, and SVG.")


if __name__ == "__main__":
    generate_plots_and_tables()
    run_scalable_simulation()
