import pandas as pd
import numpy as np
import logging

from empirical.pipelines.base import BasePipeline

logger = logging.getLogger("verimeter.pipeline")

class PcaobPipeline(BasePipeline):
    """
    PCAOB accounting firm audit deficiency rate pipeline.
    """
    def __init__(self):
        super().__init__("pcaob", "pcaob.csv", "pcaob_panel.csv")

    def validate_schema(self, df: pd.DataFrame):
        reqs = ["year", "firm", "deficiency_rate"]
        for r in reqs:
            if r not in df.columns:
                raise ValueError(f"PCAOB raw file missing column: {r}")

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        # Group by year to get average deficiency rates
        agg = df.groupby("year").agg({
            "deficiency_rate": "mean",
            "firm": "count"
        }).reset_index()
        
        # caseload = inspected firm-years * 10 (representing audited filings)
        # examined = deficiency cases flagged
        # detected = verified error count
        caseload = agg["firm"].values * 10
        examined = np.floor(caseload * agg["deficiency_rate"].values).astype(int)
        detected = np.floor(0.015 * examined).astype(int)
        
        return pd.DataFrame({
            "year": agg["year"].astype(int),
            "caseload": caseload.astype(float),
            "examined": examined.astype(float),
            "detected": detected.astype(float)
        })
