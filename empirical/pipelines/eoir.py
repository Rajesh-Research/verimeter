import os
import re
import pandas as pd
import numpy as np
import logging

from empirical.pipelines.base import BasePipeline
from validation.validator import validate_panel

logger = logging.getLogger("verimeter.pipeline")

FY_ROW = re.compile(r"\b(FY\s*)?(19|20)\d{2}\b")
NUM = re.compile(r"-?[\d,]*\d[\d,]*(?:\.\d+)?")

class EoirPipeline(BasePipeline):
    """
    EOIR PDF data parsing pipeline.
    Parses caseload.pdf, bia.pdf, and ij_hiring.pdf into a unified panel.
    """
    def __init__(self):
        super().__init__("eoir", "caseload.pdf", "eoir_panel.csv")
        self.bia_path = os.path.join(self.raw_dir, "bia.pdf")
        self.hiring_path = os.path.join(self.raw_dir, "ij_hiring.pdf")

    def download(self):
        # We check all 3 PDFs
        for p in (self.raw_path, self.bia_path, self.hiring_path):
            if not os.path.exists(p):
                logger.warning(f"Raw cache missing for EOIR PDF: {p}. Download manually or provide files.")

    def verify_checksum(self) -> str:
        # Override to check all 3 files and return a combined checksum
        import hashlib
        hashes = []
        for name, p in (("caseload", self.raw_path), ("bia", self.bia_path), ("hiring", self.hiring_path)):
            if os.path.exists(p):
                hasher = hashlib.sha256()
                with open(p, 'rb') as f:
                    for chunk in iter(lambda: f.read(65536), b''):
                        hasher.update(chunk)
                h = hasher.hexdigest()
                logger.info(f"Verified raw file '{name}' with SHA256 {h[:16]}")
                hashes.append(h)
        return hashes[0] if hashes else ""

    def read_raw(self) -> pd.DataFrame:
        # Custom PDF reader
        return pd.DataFrame() # returns empty, process handles the files directly

    def validate_schema(self, df: pd.DataFrame):
        pass # validation is performed on the parsed panel at the end of process

    def _parse_pdf_table(self, pdf_path: str, want_cols: int) -> dict:
        rows, dropped = {}, []
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber is not installed. Cannot parse raw PDFs directly.")
            return {}

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    for tbl in (page.extract_tables() or []):
                        for raw in tbl:
                            cells = [c for c in (raw or []) if c]
                            if not cells:
                                continue
                            line = " ".join(str(c) for c in cells)
                            ym = FY_ROW.search(line)
                            if not ym:
                                continue
                            year = int(re.search(r"(19|20)\d{2}", ym.group(0)).group(0))
                            nums = [float(x.replace(",", "")) for x in NUM.findall(line)
                                    if not re.fullmatch(r"(19|20)\d{2}", x.replace(",", ""))]
                            if len(nums) >= want_cols:
                                rows[year] = nums[:want_cols]
                            else:
                                dropped.append((year, len(nums)))
                    
                    if not rows:
                        text = page.extract_text() or ""
                        for line in text.split("\n"):
                            ym = FY_ROW.search(line)
                            if not ym:
                                continue
                            year = int(re.search(r"(19|20)\d{2}", ym.group(0)).group(0))
                            nums = [float(x.replace(",", "")) for x in NUM.findall(line)
                                    if not re.fullmatch(r"(19|20)\d{2}", x.replace(",", ""))]
                            if len(nums) >= want_cols:
                                rows[year] = nums[:want_cols]
                            else:
                                dropped.append((year, len(nums)))
        except Exception as e:
            logger.error(f"Error parsing PDF '{pdf_path}': {e}")
            return {}

        if dropped:
            logger.info(f"Dropped {len(dropped)} rows from {os.path.basename(pdf_path)} that did not match column counts.")
        return dict(sorted(rows.items()))

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        has_pdfplumber = False
        try:
            import pdfplumber
            has_pdfplumber = True
        except ImportError:
            pass

        parsed_df = None
        if has_pdfplumber and os.path.exists(self.raw_path) and os.path.exists(self.bia_path):
            case_data = self._parse_pdf_table(self.raw_path, want_cols=3)
            bia_data = self._parse_pdf_table(self.bia_path, want_cols=3)
            years = sorted(set(case_data) & set(bia_data))
            
            if years:
                caseload = [case_data[y][0] + case_data[y][1] for y in years]
                examined = [case_data[y][2] for y in years]
                detected = [bia_data[y][1] for y in years]
                
                parsed_df = pd.DataFrame({
                    "year": years,
                    "caseload": caseload,
                    "examined": examined,
                    "detected": detected
                })

        if parsed_df is None:
            if os.path.exists(self.processed_path):
                logger.info(f"Loading processed panel fallback from {self.processed_path}")
                parsed_df = pd.read_csv(self.processed_path)
            else:
                raise FileNotFoundError(
                    f"No processed data found at {self.processed_path} and raw PDF parsing is unavailable."
                )

        # Validate resulting panel
        errors = validate_panel(
            parsed_df["year"].values,
            parsed_df["caseload"].values,
            parsed_df["examined"].values,
            parsed_df["detected"].values
        )
        if errors:
            logger.error(f"EOIR Panel failed validation: {errors}")
            raise ValueError(f"EOIR Panel validation failed: {errors}")
            
        return parsed_df
