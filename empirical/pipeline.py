import os
import logging
import pandas as pd

# Import modular pipelines
from empirical.pipelines.eoir import EoirPipeline
from empirical.pipelines.uspto import UsptoPipeline
from empirical.pipelines.ptab import PtabPipeline
from empirical.pipelines.fda import FdaPipeline
from empirical.pipelines.eudsa import EudsaPipeline
from empirical.pipelines.clinvar import ClinvarPipeline
from empirical.pipelines.pcaob import PcaobPipeline
from empirical.pipelines.hospital import HospitalPipeline
from empirical.pipelines.asrs import AsrsPipeline

logger = logging.getLogger("verimeter.pipeline")

# Mapping of pipeline names to their respective classes
PIPELINES = {
    "eoir": EoirPipeline,
    "uspto": UsptoPipeline,
    "ptab": PtabPipeline,
    "fda": FdaPipeline,
    "eudsa": EudsaPipeline,
    "clinvar": ClinvarPipeline,
    "pcaob": PcaobPipeline,
    "hospital": HospitalPipeline,
    "asrs": AsrsPipeline
}

def run_pipeline() -> pd.DataFrame:
    """
    Primary entrypoint (default EOIR pipeline).
    Keeps backwards compatibility with experiments/runner.py.
    """
    return EoirPipeline().run()


def run_all_pipelines() -> dict:
    """
    Runs all 9 institutional database pipelines.
    
    Returns:
        dict: maps pipeline name to processed panel DataFrame
    """
    logger.info("=== Starting Execution of All 9 Institutional Pipelines ===")
    results = {}
    
    for name, pipeline_cls in PIPELINES.items():
        try:
            pipeline = pipeline_cls()
            df = pipeline.run()
            results[name] = df
        except Exception as e:
            logger.error(f"Pipeline '{name}' failed: {e}")
            raise e
            
    logger.info("=== Completed All 9 Institutional Pipelines Successfully ===")
    return results


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s][%(name)s][%(levelname)s] - %(message)s"
    )
    run_all_pipelines()
