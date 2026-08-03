import os

class Settings:
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "verimeter_industrial_grade_secret_key_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    
    # Database
    # Default to SQLite for seamless local execution; can be overridden by environment variable for PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./verimeter.db")
    
    # Celery & Redis
    # Redis broker URL; falls back to standard memory mock queue if redis is not running
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    
    # Run Celery tasks synchronously (in-process) if CELERY_ALWAYS_EAGER is True (useful for tests/no-Redis systems)
    CELERY_ALWAYS_EAGER: bool = os.getenv("CELERY_ALWAYS_EAGER", "True") == "True"

settings = Settings()
