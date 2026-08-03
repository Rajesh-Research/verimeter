from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from verimeter.backend.config import settings

# SQLite connection args mapping
connect_args = {}
engine_kwargs = {}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine_kwargs = {"connect_args": connect_args}
else:
    # Production-grade PostgreSQL connection pooling
    engine_kwargs = {
        "pool_size": 15,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800
    }

engine = create_engine(
    settings.DATABASE_URL, **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    SQLAlchemy dependency injection helper.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
