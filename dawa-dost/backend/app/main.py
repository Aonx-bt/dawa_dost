import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.routers import calls, dashboard, demo, medications, prescriptions, voice, webhooks
from app.seed import seed
from app.services.scheduler import reminder_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dawa_dost.main")

settings = get_settings()

app = FastAPI(
    title="Dawa Dost API",
    description=(
        "Medication adherence platform: prescription extraction, medication "
        "scheduling, and Sarvam Samvaad voice reminder orchestration. This is "
        "a medication-adherence tool, not a diagnostic or prescribing system."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_dir = Path(__file__).resolve().parents[1] / "uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

app.include_router(prescriptions.router)
app.include_router(medications.router)
app.include_router(voice.router)
app.include_router(webhooks.router)
app.include_router(dashboard.router)
app.include_router(calls.router)
app.include_router(demo.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if settings.demo_mode:
            seed(db)
    finally:
        db.close()
    reminder_scheduler.start()
    reminder_scheduler.process_due_reminders()
    logger.info("Dawa Dost API started (demo_mode=%s)", settings.demo_mode)


@app.on_event("shutdown")
def on_shutdown():
    reminder_scheduler.shutdown()
