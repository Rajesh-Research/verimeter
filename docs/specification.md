# Verification Standards Unit (VSU) Specification v1.0.0
## Standards for Institutional Verification Diagnostics and Quality Reporting

### 1. Introduction
This specification defines the standards for measuring, auditing, and disclosing quality metrics and verification volumes across regulatory, public, and private institutions. Its primary goal is to mitigate measurement bias (e.g. the Backlog Illusion), transparency penalties, and metric gaming.

---

### 2. Core Metrics Definition
1. **Caseload ($\lambda_t$):** The total volume of pending cases at the start of period $t$ plus new cases received during period $t$.
2. **Examinations ($\kappa_t$):** The total volume of cases that went through the verification function (e.g. finalized, audited, or examined) during period $t$.
3. **Examined Share (Coverage, $p_t$):** Defined as $p_t = \kappa_t / \lambda_t$. For census reporting, no sampling interval applies.
4. **Capacity Elasticity ($\beta$):** The elasticity of verification capacity to caseload, estimated via log-log regression:
   $$\log \kappa_t = \alpha + \beta \log \lambda_t + u_t$$
   Estimates must pass an Engle-Granger residual-based cointegration test to guard against spurious trends.
5. **Verification Depth ($\delta_t$):** The probability that an examined error is recognized by the reviewer.
6. **True Error Rate ($q_t$):** The underlying error rate in the caseload population.

---

### 3. Mitigating Gaming
To prevent institutions from inflating examined share ($\kappa/\lambda$) through cursory or meaningless reviews (which would otherwise degrade depth $\delta$), VSU mandates the following safeguards:
* **Evidence-Based Definition of Examination:** An examination is valid under this standard only if it produces an auditable, persistent checklist or verification record. A check that leaves no digital artifact is not counted.
* **Paired Parameter Reporting:** Any publication of Examined Share must be paired with the estimated verification depth ($\delta$). Cursory reviews will inflate $\kappa$ but lower $\delta$, making the degradation visible.
* **Vector Quality Dashboard:** Institutions must publish the full vector $(\kappa_t, \delta_t, q_t)$ separately rather than collapsing performance into a single scalar ranking.

---

### 4. Transparency Tiers
To prevent the "Transparency Penalty" (where honest institutions are punished for reporting bad scores while silent ones escape scrutiny), VSU establishes three Transparency Tiers:

* **Tier 1 (Full Disclosing):** Reports all three primitives ($\lambda, \kappa, D$) and operates an independent second-screen audit enabling the estimation of $q$ and $\delta$.
* **Tier 2 (Basic Disclosing):** Reports caseload $\lambda$ and examinations $\kappa$, but has no independent second screen (underlying error rate $q$ is not identified).
* **Tier 3 (Non-Reporter):** Fails to report examinations ($\kappa$) or caseload ($\lambda$). VSU will list these institutions explicitly under the "Non-Reporter" category rather than omitting them or imputing fake scores. Absence of reporting is presented as the primary finding.
