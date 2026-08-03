from celery import Celery
import json
import logging

from verimeter.backend.config import settings

logger = logging.getLogger("verimeter.backend.tasks")

# Initialize Celery app
celery_app = Celery(
    "verimeter_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Apply eager settings (run tasks synchronously by default on dev machine)
celery_app.conf.update(
    task_always_eager=settings.CELERY_ALWAYS_EAGER,
    task_eager_propagates=True
)

@celery_app.task(bind=True)
def task_run_pipeline(self, dataset_name: str) -> str:
    """
    Celery task that runs the empirical pipeline for a specific database.
    """
    logger.info(f"Starting pipeline task for dataset: {dataset_name}")
    from empirical.pipeline import PIPELINES
    
    if dataset_name not in PIPELINES:
        raise ValueError(f"Unknown dataset pipeline: {dataset_name}")
        
    pipeline_cls = PIPELINES[dataset_name]
    pipeline = pipeline_cls()
    df = pipeline.run()
    
    metadata = {
        "status": "success",
        "rows": len(df),
        "columns": list(df.columns)
    }
    return json.dumps(metadata)


@celery_app.task(bind=True)
def task_run_simulation(self, params_json: str) -> str:
    """
    Celery task that runs a scalable simulation based on custom inputs.
    """
    logger.info("Starting simulation task...")
    params = json.loads(params_json)
    
    from simulation.engine import SimulationEngine
    from simulation.policy import CapacityBooster, QualityTraining
    
    n_institutions = params.get("n_institutions", 100)
    n_periods = params.get("n_periods", 12)
    
    engine = SimulationEngine(n_institutions=n_institutions, n_periods=n_periods)
    
    # Optional policies
    hb_pct = params.get("hiring_boost_pct")
    hb_period = params.get("hiring_period")
    if hb_pct and hb_period:
        engine.add_policy(CapacityBooster(start_period=hb_period, hiring_increase_pct=hb_pct))
        
    qt_pct = params.get("quality_training_pct")
    qt_period = params.get("training_period")
    if qt_pct and qt_period:
        engine.add_policy(QualityTraining(start_period=qt_period, quality_improvement_pct=qt_pct))
        
    engine.run(
        growth_lambda=params.get("growth_lambda", 0.05),
        growth_staff=params.get("growth_staff", 0.01)
    )
    
    df = engine.get_summary_df()
    metadata = {
        "status": "success",
        "institutions": n_institutions,
        "periods": n_periods,
        "final_mean_caseload": float(df["caseload"].iloc[-1])
    }
    return json.dumps(metadata)
