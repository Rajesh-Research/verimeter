from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from verimeter.backend.database import get_db
from verimeter.backend.models import User, Job
from verimeter.backend.schemas import SimulationRunRequest, JobResponse
from verimeter.backend.routers.auth import get_current_user
from verimeter.backend.tasks import task_run_simulation

router = APIRouter(prefix="/simulations", tags=["simulations"])

@router.post("/run", response_model=JobResponse)
def run_simulation(
    req: SimulationRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    params = {
        "n_institutions": req.n_institutions,
        "n_periods": req.n_periods,
        "growth_lambda": req.growth_lambda,
        "growth_staff": req.growth_staff,
        "hiring_boost_pct": req.hiring_boost_pct,
        "hiring_period": req.hiring_period,
        "quality_training_pct": req.quality_training_pct,
        "training_period": req.training_period
    }
    
    # Schedule Celery background job
    task = task_run_simulation.delay(json.dumps(params))
    
    job = Job(
        name=f"simulation_{req.n_institutions}_inst",
        status="RUNNING",
        task_id=task.id,
        owner_id=current_user.id
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return job


@router.get("/jobs/list", response_model=list[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Job).all()
