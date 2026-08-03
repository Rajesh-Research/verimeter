from __future__ import annotations
import warnings
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from scipy import stats

# Import backend statistical modules
from verimeter.stats.regression import (
    fit_ols,
    compute_hac_se,
    compute_outlier_diagnostics,
    correct_measurement_error
)
from verimeter.stats.cointegration import (
    compute_adf_resid_t,
    get_engle_granger_critical
)
from verimeter.stats.capture_recapture import (
    estimate_two_screen,
    compute_dependence_bound,
    estimate_three_screen,
    compute_overlap_required
)


# =========================================================== Input Validation Helper
def _clean(name, x, positive=True, min_len=1):
    a = np.asarray(x, dtype=float).ravel()
    if a.size < min_len:
        raise ValueError(f"{name}: need at least {min_len} periods, got {a.size}")
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{name}: NaN or infinite at index "
                         f"{np.where(~np.isfinite(a))[0].tolist()}")
    if positive and np.any(a <= 0):
        raise ValueError(
            f"{name}: non-positive at index {np.where(a <= 0)[0].tolist()}. "
            "Zero examinations cannot be logged. Drop those periods explicitly "
            "and report that you did, rather than letting the tool decide.")
    return a


# =========================================================== Coverage (Examined Share)
@dataclass
class ExaminedShare:
    share: np.ndarray
    caseload: np.ndarray
    examined: np.ndarray
    is_census: bool
    ci_low: Optional[np.ndarray] = None
    ci_high: Optional[np.ndarray] = None

    def summary(self) -> str:
        s = self.share
        base = (f"mean {s.mean():.4f}, range [{s.min():.4f}, {s.max():.4f}], "
                f"{'FALLING' if s[-1] < s[0] else 'rising'} "
                f"{100 * (s[-1] / s[0] - 1):+.1f}% over the panel")
        if self.is_census:
            return base + "   [census: no sampling interval applies]"
        return base + (f"   [sampled: final-period CI "
                       f"({self.ci_low[-1]:.4f}, {self.ci_high[-1]:.4f})]")


def examined_share(caseload, examined, kappa_is_sample=False, alpha=0.05):
    lam = _clean("caseload", caseload)
    kap = _clean("examined", examined)
    if lam.size != kap.size:
        raise ValueError("caseload and examined differ in length")
    if np.any(kap > lam):
        raise ValueError(f"examined exceeds caseload at index "
                         f"{np.where(kap > lam)[0].tolist()}")
    p = kap / lam
    if not kappa_is_sample:
        return ExaminedShare(p, lam, kap, True)
    z = stats.norm.ppf(1 - alpha / 2)
    den = 1 + z ** 2 / lam
    ctr = (p + z ** 2 / (2 * lam)) / den
    half = z * np.sqrt(p * (1 - p) / lam + z ** 2 / (4 * lam ** 2)) / den
    return ExaminedShare(p, lam, kap, False,
                         np.clip(ctr - half, 0, 1), np.clip(ctr + half, 0, 1))


# =========================================================== Capacity Elasticity (Scaling)
@dataclass
class CapacityElasticity:
    beta: float
    se: float
    ci: tuple
    c: float
    r2: float
    n: int
    p_beta_eq_1: float
    p_beta_eq_0: float
    cointegrated: Optional[bool]
    adf_resid_t: float
    lambda_range: float
    verdict: str
    reliable: bool
    cooks_d: np.ndarray = field(default_factory=lambda: np.array([]))
    dfbetas: np.ndarray = field(default_factory=lambda: np.array([]))
    leverage: np.ndarray = field(default_factory=lambda: np.array([]))


def capacity_elasticity(caseload, examined, alpha=0.05,
                        require_cointegration=True) -> CapacityElasticity:
    lam = _clean("caseload", caseload, min_len=8)
    kap = _clean("examined", examined, min_len=8)
    if lam.size != kap.size:
        raise ValueError("caseload and examined differ in length")
    x, y = np.log(lam), np.log(kap)
    n = len(x)
    if float(np.std(x)) < 1e-10:
        raise ValueError("caseload has no variation; beta is not estimable.")

    lam_range = float(lam.max() / lam.min())
    
    # Fit linear OLS via regression module
    fit = fit_ols(x, y)
    beta_hat = fit["slope"]
    resid = fit["residuals"]
    
    # Compute Newey-West HAC standard error
    se = compute_hac_se(x, resid)
    if not np.isfinite(se) or se <= 0:
        se = fit["stderr"]
        
    tcrit = stats.t.ppf(1 - alpha / 2, max(n - 2, 1))
    ci = (beta_hat - tcrit * se, beta_hat + tcrit * se)
    p1 = float(2 * (1 - stats.t.cdf(abs(beta_hat - 1) / se, max(n - 2, 1))))
    p0 = float(2 * (1 - stats.t.cdf(abs(beta_hat - 0) / se, max(n - 2, 1))))

    # Residual-based cointegration test using cointegration module
    t_adf = compute_adf_resid_t(resid)
    eg_cv = get_engle_granger_critical(n)
    coint = None if not np.isfinite(t_adf) else bool(t_adf < eg_cv)

    # Compute Cook's Distance and DFBETAS outlier diagnostics
    outliers = compute_outlier_diagnostics(x, y)

    reliable = True
    if lam_range < 1.5:
        verdict = (f"UNINFORMATIVE: caseload varies by only {lam_range:.2f}x. "
                   "Too little variation to identify beta.")
        reliable = False
    elif require_cointegration and coint is False:
        verdict = ("SPURIOUS: log-kappa and log-lambda are not cointegrated "
                   f"(Engle-Granger t = {t_adf:.2f} vs 5% critical {eg_cv:.2f}). "
                   "The apparent relation "
                   "is a shared trend, not a response of capacity to caseload. "
                   "No verdict issued.")
        reliable = False
    elif ci[0] <= 0.0 and ci[1] >= 1.0:
        verdict = (f"UNDERPOWERED: interval [{ci[0]:.3f}, {ci[1]:.3f}] admits "
                   "both flat capacity (beta=0) and proportional staffing "
                   "(beta=1). This panel cannot tell them apart.")
        reliable = False
    elif p1 < alpha and beta_hat < 1:
        how = "flat" if p0 > alpha else "sub-proportional"
        verdict = (f"INVERSION CONFIRMED (beta = {beta_hat:.3f}, H0 beta=1 "
                   f"rejected p = {p1:.4f}; capacity is {how}). Recorded error "
                   "rate falls as load rises, at constant true quality.")
    elif p1 < alpha and beta_hat > 1:
        verdict = (f"REVERSE (beta = {beta_hat:.3f} > 1): capacity grows "
                   "faster than load. Verify how kappa was defined.")
    else:
        verdict = (f"NO INVERSION: cannot reject proportional staffing "
                   f"(beta = {beta_hat:.3f}, p = {p1:.4f}).")

    return CapacityElasticity(beta_hat, se, ci,
                               float(np.exp(fit["intercept"])), fit["r_squared"],
                               n, p1, p0, coint, float(t_adf), lam_range,
                               verdict, reliable,
                               outliers["cooks_d"], outliers["dfbetas"], outliers["leverage"])


def attenuation_bound(beta_hat, caseload, meas_error_sd_log_lambda) -> dict:
    return correct_measurement_error(beta_hat, np.log(caseload), 1.0, meas_error_sd_log_lambda)


def caseload_information(beta, caseload, examined, dq) -> float:
    if beta <= 0:
        return 0.0
    lam = float(np.mean(_clean("caseload", caseload)))
    kap = float(np.mean(_clean("examined", examined)))
    c = kap / lam ** beta
    dq = float(np.clip(dq, 1e-9, 1 - 1e-9))

    def I(b):
        k = c * lam ** b
        return (c * b * lam ** (b - 1) * dq) ** 2 / (k * dq * (1 - dq))

    return float(I(beta) / I(1.0))


# =========================================================== Verification Depth (Two Screen)
@dataclass
class TwoScreenEstimate:
    delta1: float
    delta2: float
    delta1_ci: tuple
    q: float
    q_ci: tuple
    n_true_errors: float
    se_conditional: float
    se_total: float
    n_overlap: int
    notes: list = field(default_factory=list)

    def summary(self) -> str:
        s = (f"delta (screen 1) = {self.delta1:.4f} "
             f"[{self.delta1_ci[0]:.4f}, {self.delta1_ci[1]:.4f}]\n"
             f"delta (screen 2) = {self.delta2:.4f}\n"
             f"true error rate q = {self.q:.5f} "
             f"[{self.q_ci[0]:.5f}, {self.q_ci[1]:.5f}]\n"
             f"estimated true errors = {self.n_true_errors:.1f} of "
             f"{self.n_overlap} overlap cases\n"
             f"SE conditional on N = {self.se_conditional:.2f}; "
             f"total SE = {self.se_total:.2f}")
        for n in self.notes:
            s += f"\n  ! {n}"
        return s


def two_screen(n11, n10, n01, n_overlap, alpha=0.05) -> TwoScreenEstimate:
    est = estimate_two_screen(n11, n10, n01, n_overlap, alpha)
    return TwoScreenEstimate(
        est["delta1"], est["delta2"], est["delta1_ci"],
        est["q"], est["q_ci"], est["n_true_errors"],
        est["se_conditional"], est["se_total"], est["n_overlap"], est["notes"]
    )


def dependence_bound(q_hat, rho_grid=(0.0, 0.3, 0.6, 0.9)) -> dict:
    return compute_dependence_bound(q_hat, rho_grid)


# =========================================================== Three Screen
def three_screen(counts: dict, n_overlap, alpha=0.05) -> dict:
    return estimate_three_screen(counts, n_overlap, alpha)


def overlap_required(delta_from, delta_to, q, power=0.80, alpha=0.05) -> dict:
    return compute_overlap_required(delta_from, delta_to, q, power, alpha)


# =========================================================== Verification Report
@dataclass
class VerificationReport:
    coverage: ExaminedShare
    elasticity: CapacityElasticity
    depth: Optional[TwoScreenEstimate]
    reported_rate: np.ndarray
    notes: list

    def __str__(self):
        e = self.elasticity
        L = ["=" * 76, "INSTITUTIONAL VERIFICATION REPORT",
             "verimeter 1.0.0", "=" * 76, "",
             "COVERAGE", "  " + self.coverage.summary(), "",
             "CAPACITY SCALING",
             f"  beta = {e.beta:.4f}   HAC se {e.se:.4f}   95% CI "
             f"[{e.ci[0]:.4f}, {e.ci[1]:.4f}]",
             f"  H0 beta=1: p = {e.p_beta_eq_1:.4f}    H0 beta=0: p = {e.p_beta_eq_0:.4f}",
             f"  caseload range {e.lambda_range:.2f}x    cointegrated: {e.cointegrated}"
             f"    EG t {e.adf_resid_t:.2f}",
             f"  {e.verdict}", ""]
        r = self.reported_rate
        L += ["REPORTED ERROR RATE (what the dashboard shows)",
              f"  {r[0]:.6f} -> {r[-1]:.6f}   ({100 * (r[-1] / r[0] - 1):+.1f}%)"]
        if r[-1] < r[0] and e.reliable and e.p_beta_eq_1 < 0.05 and e.beta < 1:
            L += ["  WARNING: reported rate improved while examined share fell.",
                  "  Consistent with CONSTANT or DETERIORATING true quality.",
                  "  The improvement is not evidence of improvement."]
        elif r[-1] < r[0] and not e.reliable:
            L += ["  Reported rate fell, but the capacity estimate is not",
                  "  reliable, so no inference about true quality is warranted."]
        L += ["", "DEPTH"]
        if self.depth is None:
            L += ["  NOT IDENTIFIED. delta and q enter the likelihood only as",
                  "  their product. No sample size separates them.",
                  "  Supply a second independent screen."]
        else:
            L += ["  " + x for x in self.depth.summary().split("\n")]
        if self.notes:
            L += ["", "NOTES"] + ["  - " + n for n in self.notes]
        L.append("=" * 76)
        return "\n".join(L)


def diagnose(caseload, examined, detected, second_screen=None,
             kappa_is_sample=False, alpha=0.05,
             require_cointegration=True) -> VerificationReport:
    lam = _clean("caseload", caseload, min_len=8)
    kap = _clean("examined", examined, min_len=8)
    det = _clean("detected", detected, positive=False, min_len=8)
    if not (lam.size == kap.size == det.size):
        raise ValueError("caseload, examined and detected must be equal length")
    if np.any(det > kap):
        raise ValueError(f"detected exceeds examined at index "
                         f"{np.where(det > kap)[0].tolist()}")
    cov = examined_share(lam, kap, kappa_is_sample, alpha)
    ela = capacity_elasticity(lam, kap, alpha, require_cointegration)
    notes = []
    dq = float(np.mean(det / kap))
    if ela.reliable:
        notes.append(f"detected errors carry "
                     f"{100 * caseload_information(ela.beta, lam, kap, dq):.2f}% "
                     "of the information about caseload they would carry under "
                     "proportional staffing.")
    depth = None
    if second_screen:
        depth = two_screen(alpha=alpha, **second_screen)
    else:
        notes.append("no second screen: delta and q not separately identified.")
    return VerificationReport(cov, ela, depth, det / lam, notes)
