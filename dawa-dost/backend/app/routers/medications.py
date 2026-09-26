from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AdherenceEvent, Medication, Reminder, User
from app.schemas.schemas import MedicationOut, ReminderOut
from app.utils.current_user import get_current_user
from app.utils.errors import not_found

router = APIRouter(prefix="/api/medications", tags=["medications"])


@router.get("", response_model=list[MedicationOut])
def list_medications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Medication)
        .filter(Medication.user_id == user.id)
        .order_by(Medication.created_at.desc())
        .all()
    )


@router.get("/{medication_id}", response_model=MedicationOut)
def get_medication(medication_id: str, db: Session = Depends(get_db)):
    medication = db.get(Medication, medication_id)
    if not medication:
        raise not_found("Medication")
    return medication


@router.get("/{medication_id}/reminders", response_model=list[ReminderOut])
def get_medication_reminders(medication_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Reminder)
        .filter(Reminder.medication_id == medication_id)
        .order_by(Reminder.scheduled_at.asc())
        .all()
    )


@router.get("/{medication_id}/adherence")
def get_medication_adherence(medication_id: str, db: Session = Depends(get_db)):
    medication = db.get(Medication, medication_id)
    if not medication:
        raise not_found("Medication")

    total_reminders = (
        db.query(Reminder).filter(Reminder.medication_id == medication_id).count()
    )
    taken = (
        db.query(AdherenceEvent)
        .filter(AdherenceEvent.medication_id == medication_id, AdherenceEvent.status == "TAKEN")
        .count()
    )
    adherence_percent = round((taken / total_reminders) * 100, 1) if total_reminders else 0.0
    events = (
        db.query(AdherenceEvent)
        .filter(AdherenceEvent.medication_id == medication_id)
        .order_by(AdherenceEvent.reported_at.desc())
        .all()
    )
    return {
        "medication_id": medication_id,
        "adherence_percent": adherence_percent,
        "total_reminders": total_reminders,
        "taken": taken,
        "events": [
            {
                "id": e.id,
                "status": e.status,
                "scheduled_at": e.scheduled_at,
                "reported_at": e.reported_at,
                "reason": e.reason,
            }
            for e in events
        ],
    }
