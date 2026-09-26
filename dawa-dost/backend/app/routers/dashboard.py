from collections import defaultdict
from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AdherenceEvent, Call, Medication, Reminder, SymptomEvent, User
from app.schemas.schemas import (
    DashboardOut,
    SymptomTrendOut,
    SymptomTrendPoint,
    TodayDoseOut,
    UserOut,
)
from app.utils.current_user import get_current_user

router = APIRouter(prefix="/api", tags=["dashboard"])


def _compute_adherence(db: Session, user_id: str) -> float:
    now = datetime.utcnow()
    due_count = (
        db.query(Reminder)
        .filter(Reminder.user_id == user_id)
        .filter(Reminder.status != "CANCELLED")
        .filter(Reminder.scheduled_at <= now)
        .count()
    )
    if due_count == 0:
        return 0.0
    taken_count = (
        db.query(AdherenceEvent)
        .filter(AdherenceEvent.user_id == user_id, AdherenceEvent.status == "TAKEN")
        .count()
    )
    return round(min(taken_count, due_count) / due_count * 100, 1)


def _today_doses(db: Session, user_id: str) -> list[TodayDoseOut]:
    today = datetime.utcnow().date()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)
    reminders = (
        db.query(Reminder)
        .filter(Reminder.user_id == user_id)
        .filter(Reminder.scheduled_at.between(start, end))
        .filter(Reminder.status != "CANCELLED")
        .order_by(Reminder.scheduled_at.asc())
        .all()
    )
    out = []
    for r in reminders:
        medication = db.get(Medication, r.medication_id)
        out.append(
            TodayDoseOut(
                reminder_id=r.id,
                medication_name=medication.name if medication else "Medication",
                dose=medication.dose if medication else None,
                scheduled_at=r.scheduled_at,
                status=r.status,
            )
        )
    return out


def _symptom_trends(db: Session, user_id: str) -> list[SymptomTrendOut]:
    events = (
        db.query(SymptomEvent)
        .filter(SymptomEvent.user_id == user_id)
        .order_by(SymptomEvent.reported_at.asc())
        .all()
    )
    grouped: dict[str, list[SymptomEvent]] = defaultdict(list)
    for e in events:
        grouped[e.symptom].append(e)
    return [
        SymptomTrendOut(
            symptom=symptom,
            points=[
                SymptomTrendPoint(reported_at=e.reported_at, severity=e.severity, trend=e.trend)
                for e in evs
            ],
        )
        for symptom, evs in grouped.items()
    ]


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = _today_doses(db, user.id)
    completed_today = sum(1 for d in today if d.status == "COMPLETED")
    recent_calls = (
        db.query(Call)
        .filter(Call.user_id == user.id)
        .order_by(Call.created_at.desc())
        .limit(5)
        .all()
    )
    return DashboardOut(
        user=UserOut.model_validate(user),
        adherence_percent=_compute_adherence(db, user.id),
        doses_completed_today=completed_today,
        doses_total_today=len(today),
        today=today,
        symptom_trends=_symptom_trends(db, user.id),
        recent_calls=recent_calls,
    )


@router.get("/progress")
def get_progress(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {
        "adherence_percent": _compute_adherence(db, user.id),
        "symptom_trends": _symptom_trends(db, user.id),
    }
