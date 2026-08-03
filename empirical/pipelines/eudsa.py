import pandas as pd
import numpy as np
import logging

from empirical.pipelines.base import BasePipeline

logger = logging.getLogger("verimeter.pipeline")

class EudsaPipeline(BasePipeline):
    """
    EU DSA transparency active users panel pipeline.
    """
    def __init__(self):
        super().__init__("eudsa", "eudsa.csv", "eudsa_panel.csv")

    def validate_schema(self, df: pd.DataFrame):
        reqs = ["year", "platform", "active_users_millions"]
        for r in reqs:
            if r not in df.columns:
                raise ValueError(f"EU DSA raw file missing column: {r}")

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        # Aggregate active user counts by year to form a panel
        agg = df.groupby("year")["active_users_millions"].sum().reset_index()
        
        # caseload = aggregate VLOP active users in EU (millions)
        # examined = 10% representing audited platforms/reports
        # detected = small sample violations
        caseload = agg["active_users_millions"].values
        examined = np.floor(0.12 * caseload).astype(int)
        detected = np.floor(0.01 * examined).astype(int)
        
        return pd.DataFrame({
            "year": agg["year"].astype(int),
            "caseload": caseload.astype(float),
            "examined": examined.astype(float),
            "detected": detected.astype(float)
        })
