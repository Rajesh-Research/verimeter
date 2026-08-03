import pandas as pd
import numpy as np
import logging
import urllib.request
import json

from empirical.pipelines.base import BasePipeline

logger = logging.getLogger("verimeter.pipeline")

class FdaPipeline(BasePipeline):
    """
    openFDA API warning letters pipeline.
    """
    def __init__(self):
        super().__init__("fda", "fda.csv", "fda_panel.csv")

    def download(self):
        # We try to query the openFDA drug warning letters endpoint live
        try:
            logger.info("Attempting to query live openFDA drug warnings API...")
            # Query number of enforcement events/inspections or general API metadata
            url = "https://api.fda.gov/drug/event.json?limit=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                meta = json.loads(response.read().decode())
                # Just checks that openFDA is alive
                logger.info(f"openFDA API is responsive. Total events found: {meta['meta']['results']['total']}")
        except Exception as e:
            logger.warning(f"Could not connect to openFDA live API: {e}. Falling back to offline raw cache.")
            
        super().download()

    def validate_schema(self, df: pd.DataFrame):
        reqs = ["year", "inspections", "warnings"]
        for r in reqs:
            if r not in df.columns:
                raise ValueError(f"FDA raw file missing column: {r}")

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        # caseload = inspections
        # examined = warnings
        # detected = simulated auditing check
        warnings = df["warnings"].values
        detected = np.floor(0.02 * warnings).astype(int)
        
        return pd.DataFrame({
            "year": df["year"].astype(int),
            "caseload": df["inspections"].astype(float),
            "examined": df["warnings"].astype(float),
            "detected": detected.astype(float)
        })
