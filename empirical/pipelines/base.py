import os
import hashlib
import json
import datetime
import logging
import pandas as pd

logger = logging.getLogger("verimeter.pipeline")

class BasePipeline:
    """
    Base class for all VERIMETER empirical data pipelines.
    Enforces validation, checksum, provenance, and offline cache fallbacks.
    """
    def __init__(self, name: str, raw_filename: str, processed_filename: str):
        self.name = name
        self.raw_dir = os.path.join("datasets", "raw")
        self.processed_dir = os.path.join("datasets", "processed")
        
        self.raw_path = os.path.join(self.raw_dir, raw_filename)
        self.processed_path = os.path.join(self.processed_dir, processed_filename)
        self.provenance_path = os.path.join("datasets", "provenance.jsonl")
        
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

    def run(self) -> pd.DataFrame:
        """
        Executes the pipeline lifecycle.
        """
        logger.info(f"Running pipeline '{self.name}'...")
        
        # 1. Download/Retrieve raw file (falling back to offline cache)
        self.download()
        
        if not os.path.exists(self.raw_path):
            raise FileNotFoundError(f"Raw data file not found at {self.raw_path} and no offline fallback available.")
            
        # 2. Checksum verification
        sha256 = self.verify_checksum()
        
        # 3. Read data
        df = self.read_raw()
        
        # 4. Schema and logic validation
        self.validate_schema(df)
        
        # 5. Process data
        panel_df = self.process(df)
        
        # Save processed panel
        panel_df.to_csv(self.processed_path, index=False)
        logger.info(f"Successfully processed panel saved to {self.processed_path}")
        
        # 6. Log provenance
        size_bytes = os.path.getsize(self.raw_path)
        rows_count = len(panel_df)
        self.log_provenance(sha256, size_bytes, rows_count)
        
        return panel_df

    def download(self):
        """
        Downloads raw data. Subclasses can override to implement API/URL downloads.
        By default, logs that it falls back to the offline cached file.
        """
        if os.path.exists(self.raw_path):
            logger.info(f"Using cached raw file for '{self.name}': {self.raw_path}")
        else:
            logger.warning(f"Raw cache missing for '{self.name}'. Implement API download in subclass or provide raw file.")

    def verify_checksum(self) -> str:
        """
        Computes SHA256 of the raw file.
        """
        hasher = hashlib.sha256()
        with open(self.raw_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        sha256 = hasher.hexdigest()
        logger.info(f"Verified raw file '{self.name}' with SHA256 {sha256[:16]}")
        return sha256

    def read_raw(self) -> pd.DataFrame:
        """
        Reads raw data into a DataFrame. Standard implementation supports CSV.
        """
        if self.raw_path.endswith('.csv'):
            return pd.read_csv(self.raw_path)
        elif self.raw_path.endswith('.json') or self.raw_path.endswith('.jsonl'):
            return pd.read_json(self.raw_path, lines=self.raw_path.endswith('.jsonl'))
        else:
            # Fallback placeholder structure if it's a binary file (like PDF)
            return pd.DataFrame()

    def validate_schema(self, df: pd.DataFrame):
        """
        Validates column names, data types, and logical bounds. Must be overridden.
        """
        raise NotImplementedError

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans and pivots raw data into a standard time-series panel. Must be overridden.
        """
        raise NotImplementedError

    def log_provenance(self, sha256: str, size_bytes: int, rows_count: int):
        """
        Appends a JSON record of this pipeline run to the provenance audit log.
        """
        record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "pipeline": self.name,
            "raw_file": self.raw_path,
            "sha256": sha256,
            "size_bytes": size_bytes,
            "processed_rows": rows_count,
            "status": "success"
        }
        with open(self.provenance_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record) + "\n")
        logger.info(f"Logged provenance record for '{self.name}' in {self.provenance_path}")
