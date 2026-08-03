import numpy as np
from simulation.institution import InstitutionPanel

class PolicyIntervention:
    """
    Defines policy shifts that modify the parameters of simulated institutions.
    """
    def __init__(self, start_period: int):
        self.start_period = start_period

    def apply(self, panel: InstitutionPanel, t: int):
        """
        Modifies panel properties at period t.
        """
        pass

class CapacityBooster(PolicyIntervention):
    """
    Simulates a staff expansion (e.g. 50% hiring campaign) starting from a specified period.
    """
    def __init__(self, start_period: int, hiring_increase_pct: float = 0.5):
        super().__init__(start_period)
        self.hiring_increase_pct = hiring_increase_pct

    def apply(self, panel: InstitutionPanel, t: int):
        if t >= self.start_period:
            # Immediate boost in staff count
            panel.staff[:, t] *= (1.0 + self.hiring_increase_pct)

class QualityTraining(PolicyIntervention):
    """
    Simulates training programs that reduce the true error rates of institutions.
    """
    def __init__(self, start_period: int, quality_improvement_pct: float = 0.3):
        super().__init__(start_period)
        self.quality_improvement_pct = quality_improvement_pct

    def apply(self, panel: InstitutionPanel, t: int):
        if t >= self.start_period:
            # Propagate and apply true error rate quality decay
            panel.true_error_rate[:, t] = panel.true_error_rate[:, t-1] * (1.0 - self.quality_improvement_pct)
        else:
            # Otherwise true error rate remains at baseline values
            panel.true_error_rate[:, t] = panel.true_error_rate[:, t-1]
            
class DoubleScreenProtocol(PolicyIntervention):
    """
    Simulates changing verification from single screen to double screen.
    """
    def __init__(self, start_period: int, screen1_delta: float = 0.60, screen2_delta: float = 0.45):
        super().__init__(start_period)
        self.screen1_delta = screen1_delta
        self.screen2_delta = screen2_delta

    def apply(self, panel: InstitutionPanel, t: int):
        # Keeps true error rate constant, but allows capture-recapture calculations
        if t < self.start_period:
            panel.true_error_rate[:, t] = panel.true_error_rate[:, t-1]
        else:
            # Decays true error rate by 10% due to dual review compliance feedback
            panel.true_error_rate[:, t] = panel.true_error_rate[:, t-1] * 0.90
