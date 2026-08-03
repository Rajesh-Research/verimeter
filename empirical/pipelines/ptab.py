import pandas as pd
import numpy as np
import logging

from empirical.pipelines.base import BasePipeline

logger = logging.getLogger("verimeter.pipeline")

class PtabPipeline(BasePipeline):
    """
    PTAB Inter Partes Review statistics pipeline.
    """
    def __init__(self):
        super().__init__("ptab", "ptab.csv", "ptab_panel.csv")

    def validate_schema(self, df: pd.DataFrame):
        reqs = ["year", "filed", "completions"]
        for r in reqs:
            if r not in df.columns:
                raise ValueError(f"PTAB raw file missing column: {r}")

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        # caseload = filed
        # examined = completions
        # detected = simulated 1% double check audits
        completions = df["completions"].values
        detected = np.floor(0.01 * completions).astype(int)
        
        return pd.DataFrame({
            "year": df["year"].astype(int),
            "caseload": df["filed"].astype(float),
            "examined": df["completions"].astype(float),
            "detected": detected.astype(float)
        })
