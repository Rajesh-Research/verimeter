import pandas as pd
import numpy as np
import logging

from empirical.pipelines.base import BasePipeline

logger = logging.getLogger("verimeter.pipeline")

class AsrsPipeline(BasePipeline):
    """
    ASRS Aviation Safety Report incident filing pipeline.
    """
    def __init__(self):
        super().__init__("asrs", "asrs.csv", "asrs_panel.csv")

    def validate_schema(self, df: pd.DataFrame):
        reqs = ["year", "incidents", "examined"]
        for r in reqs:
            if r not in df.columns:
                raise ValueError(f"ASRS raw file missing column: {r}")

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        # caseload = incidents
        # examined = examined
        # detected = simulated serious warnings flagged
        examined = df["examined"].values
        detected = np.floor(0.015 * examined).astype(int)
        
        return pd.DataFrame({
            "year": df["year"].astype(int),
            "caseload": df["incidents"].astype(float),
            "examined": df["examined"].astype(float),
            "detected": detected.astype(float)
        })
