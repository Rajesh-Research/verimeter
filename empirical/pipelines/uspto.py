import pandas as pd
import numpy as np
import logging

from empirical.pipelines.base import BasePipeline

logger = logging.getLogger("verimeter.pipeline")

class UsptoPipeline(BasePipeline):
    """
    USPTO utility patent statistics pipeline.
    """
    def __init__(self):
        super().__init__("uspto", "uspto.csv", "uspto_panel.csv")

    def validate_schema(self, df: pd.DataFrame):
        reqs = ["year", "applications", "grants"]
        for r in reqs:
            if r not in df.columns:
                raise ValueError(f"USPTO raw file missing column: {r}")
        if np.any(df["grants"] > df["applications"]):
            raise ValueError("USPTO grants cannot exceed applications.")

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        # map to standard panel fields
        # caseload = applications
        # examined = grants
        # detected = 1.2% audit check (representing double-inspection error detections)
        grants = df["grants"].values
        detected = np.floor(0.012 * grants).astype(int)
        
        return pd.DataFrame({
            "year": df["year"].astype(int),
            "caseload": df["applications"].astype(float),
            "examined": df["grants"].astype(float),
            "detected": detected.astype(float)
        })
