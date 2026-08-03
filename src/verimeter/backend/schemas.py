from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    role: Optional[str] = "researcher"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Dataset Schemas
class DatasetBase(BaseModel):
    name: str

class DatasetResponse(DatasetBase):
    id: int
    raw_filename: str
    processed_filename: str
    sha256: str
    rows_count: int
    owner_id: int
    
    model_config = ConfigDict(from_attributes=True)

# Job Schemas
class JobBase(BaseModel):
    name: str

class JobResponse(JobBase):
    id: int
    status: str
    task_id: Optional[str] = None
    result_metadata: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Experiment Result Schemas
class ExperimentRunRequest(BaseModel):
    dataset_name: str
    require_cointegration: Optional[bool] = True

class ExperimentResultResponse(BaseModel):
    id: int
    dataset_name: str
    beta: float
    hac_se: float
    verdict: str
    cointegrated: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)

# Simulation Request Schema
class SimulationRunRequest(BaseModel):
    n_institutions: int = 100
    n_periods: int = 12
    growth_lambda: float = 0.05
    growth_staff: float = 0.01
    hiring_boost_pct: Optional[float] = None
    hiring_period: Optional[int] = None
    quality_training_pct: Optional[float] = None
    training_period: Optional[int] = None
