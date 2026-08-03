import pandas as pd
import numpy as np
import logging

from empirical.pipelines.base import BasePipeline

logger = logging.getLogger("verimeter.pipeline")

class ClinvarPipeline(BasePipeline):
    """
    ClinVar clinical variants pathogenicity classification pipeline.
    """
    def __init__(self):
        super().__init__("clinvar", "clinvar.csv", "clinvar_panel.csv")

    def validate_schema(self, df: pd.DataFrame):
        reqs = ["year", "variants", "reviewed"]
        for r in reqs:
            if r not in df.columns:
                raise ValueError(f"ClinVar raw file missing column: {r}")

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        # caseload = variants
        # examined = reviewed
        # detected = simulated pathogenic variants
        reviewed = df["reviewed"].values
        detected = np.floor(0.015 * reviewed).astype(int)
        
        return pd.DataFrame({
            "year": df["year"].astype(int),
            "caseload": df["variants"].astype(float),
            "examined": df["reviewed"].astype(float),
            "detected": detected.astype(float)
        })
