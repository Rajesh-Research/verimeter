from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from verimeter.backend.database import engine, Base
from verimeter.backend.routers import auth, datasets, experiments, simulations

# Initialize SQLite database tables automatically for dev execution
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VERIMETER API Platform",
    description="Industrial-grade Institutional Quality Verification Diagnostics platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Policy configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://verimeter-vsu-2026.web.app",
        "http://localhost:3000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check Route
@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "service": "verimeter-backend",
        "version": "1.0.0"
    }

# Wire router submodules under versioned prefix
api_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(datasets.router, prefix=api_prefix)
app.include_router(experiments.router, prefix=api_prefix)
app.include_router(simulations.router, prefix=api_prefix)
