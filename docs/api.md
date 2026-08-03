# API Reference & Complexity Analysis

This document details the functions, mathematical definitions, complexity analysis, and code examples for the **VERIMETER** statistical backend.

---

## 1. Diagnostics module

### `verimeter.diagnose`
```python
def diagnose(caseload, examined, detected, second_screen=None, 
             kappa_is_sample=False, alpha=0.05, 
             require_cointegration=True) -> VerificationReport
```
Orchestrates the entire capacity diagnostics workflow on input panels.
* **Complexity:**
  * **Time:** $\mathcal{O}(T \log T + T \cdot L)$ where $T$ is panel length and $L$ is Newey-West lags count.
  * **Space:** $\mathcal{O}(T)$ to hold the panel data.
* **Example:**
  ```python
  import verimeter as V
  rep = V.diagnose(caseload, examined, detected)
  print(rep)
  ```

---

## 2. Capacity Scaling Backend (`verimeter.stats.regression`)

### `fit_ols`
```python
def fit_ols(x, y) -> dict
```
Fits a simple linear OLS: $y = \alpha + \beta x + \epsilon$.
* **Mathematical Definition:**
  $$\hat{\beta} = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sum (x_i - \bar{x})^2}, \quad \hat{\alpha} = \bar{y} - \hat{\beta}\bar{x}$$
* **Complexity:**
  * **Time:** $\mathcal{O}(T)$ where $T$ is array size.
  * **Space:** $\mathcal{O}(T)$ to store residuals.
* **Example:**
  ```python
  from verimeter.stats.regression import fit_ols
  fit = fit_ols([1, 2, 3], [2, 4, 5])
  print("Slope:", fit["slope"])
  ```

### `compute_hac_se`
```python
def compute_hac_se(x, resid, nlags=None) -> float
```
Estimates Newey-West HAC standard error for regression slope.
* **Mathematical Definition:**
  $$\hat{\Gamma} = \sum_{j=-L}^{L} \left(1 - \frac{|j|}{L+1}\right) \hat{\Gamma}_j, \quad \hat{\Gamma}_j = \frac{1}{T} \sum_{t=j+1}^{T} u_t u_{t-j} x_{c,t} x_{c,t-j}$$
* **Complexity:**
  * **Time:** $\mathcal{O}(T \cdot L)$ where $L$ is lags bandwidth.
  * **Space:** $\mathcal{O}(T)$ for mean-centered array products.

### `compute_outlier_diagnostics`
```python
def compute_outlier_diagnostics(x, y) -> dict
```
Calculates Cook's Distance ($D_i$) and DFBETAS for outlier checking.
* **Mathematical Definition:**
  * Leverage: $h_i = \frac{1}{T} + \frac{(x_i - \bar{x})^2}{\sum (x_j - \bar{x})^2}$
  * Cook's Distance: $D_i = \frac{e_i^2}{2 s^2} \left( \frac{h_i}{(1 - h_i)^2} \right)$
* **Complexity:**
  * **Time:** $\mathcal{O}(T^2)$ due to leave-one-out OLS refits for DFBETAS.
  * **Space:** $\mathcal{O}(T)$.

### `correct_measurement_error`
```python
def correct_measurement_error(beta_hat, x, se_hat, meas_error_sd) -> dict
```
Adjusts $\hat{\beta}$ for measurement errors in regressor.
* **Mathematical Definition:**
  $$\gamma = 1 - \frac{\sigma_u^2}{\sigma_x^2}, \quad \beta_{\text{corrected}} = \frac{\hat{\beta}}{\gamma}$$
* **Complexity:**
  * **Time:** $\mathcal{O}(T)$ (to calculate regressor variance).
  * **Space:** $\mathcal{O}(1)$.

---

## 3. Cointegration Backend (`verimeter.stats.cointegration`)

### `compute_adf_resid_t`
```python
def compute_adf_resid_t(resid, maxlag=1) -> float
```
Computes the Dickey-Fuller t-statistic on residuals to verify stationarity.
* **Complexity:**
  * **Time:** $\mathcal{O}(T)$ for small lags.
  * **Space:** $\mathcal{O}(T)$.

### `get_engle_granger_critical`
```python
def get_engle_granger_critical(n, level=0.05) -> float
```
Returns Engle-Granger response surface critical value for cointegration:
$$\text{CV} = a + \frac{b}{n} + \frac{c}{n^2}$$
* **Complexity:** $\mathcal{O}(1)$ time, $\mathcal{O}(1)$ space.

---

## 4. Capture-Recapture Backend (`verimeter.stats.capture_recapture`)

### `estimate_two_screen`
```python
def estimate_two_screen(n11, n10, n01, n_overlap, alpha=0.05) -> dict
```
Chapman-corrected capture-recapture estimator.
* **Mathematical Definition:**
  $$\hat{N} = \frac{(n_{1\cdot} + 1)(n_{\cdot1} + 1)}{n_{11} + 1} - 1, \quad \text{var}_{\text{total}}(q) = \frac{\text{var}_{\text{cond}}(N) + n_{\text{overlap}} q(1-q)}{n_{\text{overlap}}^2}$$
* **Complexity:** $\mathcal{O}(1)$ time, $\mathcal{O}(1)$ space.

### `estimate_three_screen`
```python
def estimate_three_screen(counts: dict, n_overlap, alpha=0.05) -> dict
```
Log-linear MLE solver for three-screen setups.
* **Complexity:**
  * **Time:** $\mathcal{O}(M)$ where $M$ is the Nelder-Mead optimization steps ($\approx 200 - 500$ iterations).
  * **Space:** $\mathcal{O}(1)$ (fixed $7 \times 4$ matrices).

---

## 5. Monte Carlo & Power Backend (`verimeter.stats.monte_carlo`)

### `monte_carlo_validation`
```python
def monte_carlo_validation(n_replicates=100, n_periods=30, beta_true=0.3, q_true=0.08, 
                           delta_true=0.6, seed=42) -> dict
```
Validates parameter recovery bias and MSE using Monte Carlo replicates.
* **Complexity:** $\mathcal{O}(M \cdot T \cdot L)$ where $M$ is replicate count, $T$ is periods, and $L$ is lags.

### `compute_elasticity_power`
```python
def compute_elasticity_power(n_periods=30, beta_null=1.0, beta_alt=0.5, 
                             n_replicates=200, alpha=0.05, seed=42) -> dict
```
Computes empirical power of rejecting $H_0: \beta = \beta_{\text{null}}$ when $\beta = \beta_{\text{alt}}$.
* **Complexity:** $\mathcal{O}(M \cdot T \cdot L)$ time.
