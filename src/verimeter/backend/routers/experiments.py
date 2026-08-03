from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
import os
import pandas as pd

from verimeter.backend.database import get_db
from verimeter.backend.models import User, ExperimentResult
from verimeter.backend.schemas import ExperimentRunRequest, ExperimentResultResponse
from verimeter.backend.routers.auth import get_current_user
from verimeter.diagnostics import capacity_elasticity

router = APIRouter(prefix="/experiments", tags=["experiments"])

@router.post("/run", response_model=ExperimentResultResponse)
def run_experiment(
    req: ExperimentRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve processed panel file
    processed_path = os.path.join("datasets", "processed", f"{req.dataset_name}_panel.csv")
    if not os.path.exists(processed_path):
        raise HTTPException(status_code=404, detail=f"Processed panel not found for {req.dataset_name}. Upload and process first.")
        
    df = pd.read_csv(processed_path)
    
    # Dynamic column mapping fallback
    caseload_col = "caseload"
    examined_col = "examined"
    
    if caseload_col not in df.columns or examined_col not in df.columns:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if len(numeric_cols) >= 2:
            caseload_col = numeric_cols[0]
            examined_col = numeric_cols[1]
        elif len(df.columns) >= 2:
            caseload_col = df.columns[0]
            examined_col = df.columns[1]
        else:
            raise HTTPException(
                status_code=400,
                detail="Dataset must contain at least two columns to run verification analysis."
            )
            
    try:
        # Run verimeter capacity elasticity diagnostics on resolved columns
        ela = capacity_elasticity(
            df[caseload_col], 
            df[examined_col], 
            require_cointegration=req.require_cointegration
        )
        
        res = ExperimentResult(
            dataset_name=req.dataset_name,
            beta=ela.beta,
            hac_se=ela.se,
            verdict=ela.verdict,
            cointegrated=ela.cointegrated
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Diagnostics failed: {e}")


@router.get("/results/list", response_model=list[ExperimentResultResponse])
def list_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ExperimentResult).all()


@router.get("/exports/{result_id}/table", response_class=PlainTextResponse)
def export_latex_table(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = db.query(ExperimentResult).filter(ExperimentResult.id == result_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Result not found")
        
    coint_str = "Yes" if res.cointegrated else "No"
    
    tex = r"""\begin{tabular}{lc}
\hline
\textbf{Metric} & \textbf{Estimated Value} \\
\hline
Dataset Name & """ + res.dataset_name.upper() + r""" \\
Capacity Elasticity ($\beta$) & """ + f"{res.beta:.4f}" + r""" \\
Newey-West HAC se & """ + f"{res.hac_se:.4f}" + r""" \\
Cointegration Coherent & """ + coint_str + r""" \\
Diagnostic Verdict & """ + res.verdict + r""" \\
\hline
\end{tabular}
"""
    return tex
