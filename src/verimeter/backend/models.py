from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime

from verimeter.backend.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="researcher")
    is_active = Column(Boolean, default=True)
    
    datasets = relationship("Dataset", back_populates="owner")
    jobs = relationship("Job", back_populates="owner")


class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    raw_filename = Column(String, nullable=False)
    processed_filename = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    rows_count = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="datasets")


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, RUNNING, SUCCESS, FAILED
    task_id = Column(String, unique=True, index=True, nullable=True)
    result_metadata = Column(String, nullable=True)  # JSON-serialized metadata
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="jobs")


class ExperimentResult(Base):
    __tablename__ = "experiment_results"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String, index=True, nullable=False)
    beta = Column(Float, nullable=False)
    hac_se = Column(Float, nullable=False)
    verdict = Column(String, nullable=False)
    cointegrated = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
