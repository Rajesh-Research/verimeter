from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import hashlib

from verimeter.backend.database import get_db
from verimeter.backend.models import Dataset, User, Job
from verimeter.backend.schemas import DatasetResponse, JobResponse
from verimeter.backend.routers.auth import get_current_user
from verimeter.backend.tasks import task_run_pipeline

router = APIRouter(prefix="/datasets", tags=["datasets"])

# Define sync wrapper for background execution
def run_pipeline_sync(name: str):
    try:
        task_run_pipeline(name)
    except Exception as e:
        print(f"Error running pipeline in background: {e}")

@router.post("/upload", response_model=DatasetResponse)
def upload_dataset(
    name: str, 
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify name uniqueness
    existing = db.query(Dataset).filter(Dataset.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Dataset name already exists")
        
    raw_dir = os.path.join("datasets", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    # Save raw file
    raw_filename = f"{name}_raw.csv"
    raw_path = os.path.join(raw_dir, raw_filename)
    
    hasher = hashlib.sha256()
    content = file.file.read()
    hasher.update(content)
    sha256 = hasher.hexdigest()
    
    with open(raw_path, "wb") as f:
        f.write(content)
        
    # Standard output processed filename
    processed_filename = f"{name}_panel.csv"
    
    dataset = Dataset(
        name=name,
        raw_filename=raw_filename,
        processed_filename=processed_filename,
        sha256=sha256,
        rows_count=0,  # parsed later
        owner_id=current_user.id
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.post("/process/{name}", response_model=JobResponse)
def process_dataset(
    name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.name == name).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    # Queue parsing background task using FastAPI's native BackgroundTasks
    background_tasks.add_task(run_pipeline_sync, name)
    
    job = Job(
        name=f"process_{name}",
        status="RUNNING",
        task_id=f"fastapi_job_{name}",
        owner_id=current_user.id
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return job


@router.get("/list", response_model=list[DatasetResponse])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Dataset).all()


@router.get("/download/{name}")
def download_processed_panel(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.name == name).first()
    if not dataset:
        # Check default pipeline files as fallback
        processed_path = os.path.join("datasets", "processed", f"{name}_panel.csv")
        if os.path.exists(processed_path):
            return FileResponse(processed_path, filename=f"{name}_panel.csv")
        raise HTTPException(status_code=404, detail="Processed dataset panel not found")
        
    processed_path = os.path.join("datasets", "processed", dataset.processed_filename)
    if not os.path.exists(processed_path):
         raise HTTPException(status_code=404, detail="Processed panel file does not exist on disk yet. Trigger process first.")
         
    return FileResponse(processed_path, filename=dataset.processed_filename)
