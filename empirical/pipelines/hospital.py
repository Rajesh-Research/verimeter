import pandas as pd
import numpy as np
import logging

from empirical.pipelines.base import BasePipeline

logger = logging.getLogger("verimeter.pipeline")

class HospitalPipeline(BasePipeline):
    """
    Medicare Hospital Compare CMS quality indices pipeline.
    """
    def __init__(self):
        super().__init__("hospital", "hospital.csv", "hospital_panel.csv")

    def validate_schema(self, df: pd.DataFrame):
        reqs = ["year", "hospitals", "avg_rating"]
        for r in reqs:
            if r not in df.columns:
                raise ValueError(f"Hospital Compare raw file missing column: {r}")

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        # caseload = max possible star points (5 per hospital)
        # examined = total star points awarded (hospitals * avg_rating)
        # detected = simulated auditing review checks
        hospitals = df["hospitals"].values
        caseload = hospitals * 5.0
        examined = hospitals * df["avg_rating"].values
        detected = np.floor(0.015 * examined).astype(int)
        
        return pd.DataFrame({
            "year": df["year"].astype(int),
            "caseload": caseload.astype(float),
            "examined": examined.astype(float),
            "detected": detected.astype(float)
        })
