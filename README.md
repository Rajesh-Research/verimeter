# VERIMETER: Institutional Verification Diagnostics

VERIMETER is an industrial-grade research platform and statistical engine designed to diagnose institutional quality measurement errors. It implements diagnostics for verification coverage, capacity elasticity ($\beta$), and verification depth (Chapman-corrected capture-recapture and three-screen estimators), addressing the systematic "Backlog Illusion" where dashboards report quality improvements due to capacity constraints rather than true quality shifts.

---

## 1. Repository Structure

The platform is structured as follows:

* **`src/verimeter/`**: Core library implementation (`diagnostics.py`, `utils.py`, `logging_setup.py`).
* **`simulation/`**: Synthetic data generators and numerical verification scripts (`data_generator.py`, `run_simulations.py`).
* **`empirical/`**: Data pipelines including raw PDF ingestion, parsing, checksum verification, and fallback loaders.
* **`datasets/`**: Data storage holding `raw/` and `processed/` folders, plus the provenance audit log.
* **`experiments/`**: Runner script and Hydra YAML configuration files.
* **`validation/`**: Pre-run and post-run validation checkers.
* **`paper/`**: LaTeX draft of the manuscript and supplementary tables.
* **`figures/`**: Auto-generated publication-quality plots.
* **`tests/`**: Pytest test suite covering statistical gates, standard errors, and pipeline logic.
* **`notebooks/`**: Interactive walkthrough demonstration of the API.
* **`docs/`**: Standards specification (VSU standards) and API references.

---

## 2. Requirements & Installation

The project uses **Python >= 3.10** and **Poetry** for package management.

### Installation
To install the package and all dependencies in a local virtual environment:
```bash
poetry install
```

---

## 3. How to Run

### Run All Experiments (Simulations + Empirical Panel)
To run all simulation trials and empirical diagnostics, generating all tables and figures:
```bash
poetry run python experiments/runner.py
```
To run only the simulations:
```bash
poetry run python experiments/runner.py experiment=simulation
```
To run only the empirical EOIR workload pipeline:
```bash
poetry run python experiments/runner.py experiment=eoir
```

### Run Tests
To run all unit and statistical tests:
```bash
poetry run pytest
```

### Run with Docker
You can also run the entire reproducibility pipeline inside a Docker container:
```bash
# Build the image
docker build -t verimeter .

# Run the pipeline and mount outputs to host directory
docker run -v ${PWD}/figures:/workspace/figures -v ${PWD}/paper/tables:/workspace/paper/tables verimeter
```
