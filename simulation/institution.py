import numpy as np

class InstitutionPanel:
    """
    Manages states for a collection of simulated institutions.
    Uses vectorized numpy matrices for speed and low memory footprint,
    enabling scaling to millions of institutions.
    """
    def __init__(self, n_institutions: int, n_periods: int, seed: int = 42):
        self.n_institutions = n_institutions
        self.n_periods = n_periods
        self.seed = seed
        
        np.random.seed(seed)
        
        # Dimensions: (n_institutions, n_periods)
        self.caseload = np.zeros((n_institutions, n_periods))
        self.staff = np.zeros((n_institutions, n_periods))
        self.capacity = np.zeros((n_institutions, n_periods))
        self.true_error_rate = np.zeros((n_institutions, n_periods))
        self.examined = np.zeros((n_institutions, n_periods))
        
        # Initialize period 0
        self.caseload[:, 0] = np.random.uniform(500, 2000, n_institutions)
        self.staff[:, 0] = np.random.uniform(10, 50, n_institutions)
        self.true_error_rate[:, 0] = np.random.uniform(0.05, 0.15, n_institutions)
        
        # Review capacity per staff member (average cases resolved per staff member)
        self.review_efficiency = np.random.uniform(15, 30, n_institutions)
        
    def step_demographics(self, t: int, growth_lambda: float = 0.05, 
                          growth_staff: float = 0.0, sigma_lambda: float = 0.05):
        """
        Updates caseload and staff states for period t.
        """
        # caseload random walk with drift: lambda_t = lambda_{t-1} * exp(g + N(0, sd))
        noise = np.random.normal(0, sigma_lambda, self.n_institutions)
        self.caseload[:, t] = self.caseload[:, t-1] * np.exp(growth_lambda + noise)
        
        # staff growth: S_t = S_{t-1} * (1 + g_S)
        self.staff[:, t] = self.staff[:, t-1] * (1.0 + growth_staff)
        
    def calculate_capacity_and_reviews(self, t: int, selection_bias_alpha: float = 1.0):
        """
        Calculates review capacity, reviews completed (examined), and true error rates.
        """
        # Max capacity = staff * efficiency + noise
        noise = np.random.normal(0, 10, self.n_institutions)
        self.capacity[:, t] = np.maximum(0.0, self.staff[:, t] * self.review_efficiency + noise)
        
        # Examined (completions) = min(caseload, capacity)
        self.examined[:, t] = np.minimum(self.caseload[:, t], self.capacity[:, t])
