"""Backend APIs consumed by the Sarvam Samvaad voice agent, plus the endpoint
that triggers a call. Sarvam credentials never touch the frontend - all
Samvaad HTTP calls are isolated inside SarvamVoiceService.
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AdherenceEvent, Medication, Reminder, SideEffectEvent, SymptomEvent, User
from app.schemas.schemas import (
    MedicationSnoozeRequest,
    MedicationTakenRequest,
    SideEffectReportRequest,
    SymptomReportRequest,
    TriggerCallRequest,
    VoiceContextRequest,
)
from app.services.sarvam_voice import VoiceCallError, sarvam_voice_service
from app.services.scheduler import reminder_scheduler
from app.utils.errors import bad_request, not_found, upstream_failure

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/trigger")
def trigger_call(body: TriggerCallRequest, db: Session = Depends(get_db)):
    """Manually trigger the Samvaad call for a reminder (used by Demo Mode's
    "Call me now", and as a general-purpose trigger endpoint)."""
    reminder = db.get(Reminder, body.reminder_id)
    if not reminder:
        raise not_found("Reminder")
    medication = db.get(Medication, reminder.medication_id)
    user = db.get(User, reminder.user_id)
    if not medication or not user:
        raise bad_request("Reminder is missing its medication or user context.")

    context = {
        "user_id": user.id,
        "reminder_id": reminder.id,
        "medication_id": medication.id,
        "medication_name": medication.name,
        "dose": medication.dose,
        "food_instruction": medication.food_instruction,
        "scheduled_time": reminder.scheduled_at.strftime("%H:%M"),
    }
    try:
        interaction_id = sarvam_voice_service.trigger_call(user.phone, context)
    except VoiceCallError as exc:
        raise upstream_failure("Sarvam Samvaad", str(exc))

    reminder.status = "TRIGGERED"
    reminder.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "triggered", "interaction_id": interaction_id}


@router.post("/context")
def get_voice_context(body: VoiceContextRequest, db: Session = Depends(get_db)):
    """Samvaad calls this to fetch full context for a reminder mid-call,
    instead of receiving the entire patient record up front."""
    reminder = db.get(Reminder, body.reminder_id)
    if not reminder:
        raise not_found("Reminder")
    medication = db.get(Medication, reminder.medication_id)
    user = db.get(User, reminder.user_id)
    return {
        "medication": {
            "id": medication.id,
            "name": medication.name,
            "strength": medication.strength,
            "dose": medication.dose,
            "food_instruction": medication.food_instruction,
            "special_instruction": medication.special_instruction,
        }
        if medication
        else None,
        "reminder": {
            "id": reminder.id,
            "scheduled_at": reminder.scheduled_at,
            "status": reminder.status,
        },
        "patient": {
            "id": user.id,
            "name": user.name,
            "preferred_language": user.preferred_language,
        }
        if user
        else None,
    }


@router.post("/medication/taken")
def mark_medication_taken(body: MedicationTakenRequest, db: Session = Depends(get_db)):
    reminder = db.get(Reminder, body.reminder_id)
    if not reminder:
        raise not_found("Reminder")

    event = AdherenceEvent(
        user_id=reminder.user_id,
        medication_id=body.medication_id,
        call_id=reminder.call_id,
        scheduled_at=reminder.scheduled_at,
        status="TAKEN",
    )
    db.add(event)
    reminder.status = "COMPLETED"
    reminder.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "ok"}


@router.post("/medication/snooze")
def snooze_medication(body: MedicationSnoozeRequest, db: Session = Depends(get_db)):
    reminder = db.get(Reminder, body.reminder_id)
    if not reminder:
        raise not_found("Reminder")

    new_time = reminder_scheduler.snooze_reminder(body.reminder_id, body.minutes)

    event = AdherenceEvent(
        user_id=reminder.user_id,
        medication_id=reminder.medication_id,
        call_id=reminder.call_id,
        scheduled_at=reminder.scheduled_at,
        status="SNOOZED",
        reason=f"Snoozed {body.minutes} minutes",
    )
    db.add(event)
    db.commit()
    return {"status": "ok", "new_scheduled_at": new_time}


@router.post("/symptom")
def record_symptom(body: SymptomReportRequest, db: Session = Depends(get_db)):
    event = SymptomEvent(
        user_id=body.user_id,
        call_id=body.call_id,
        symptom=body.symptom,
        severity=body.severity,
        trend=body.trend,
        source="PATIENT_REPORTED",
    )
    db.add(event)
    db.commit()
    return {"status": "ok"}


@router.post("/side-effect")
def record_side_effect(body: SideEffectReportRequest, db: Session = Depends(get_db)):
    event = SideEffectEvent(
        user_id=body.user_id,
        call_id=body.call_id,
        symptom=body.symptom,
        severity=body.severity,
    )
    db.add(event)
    db.commit()
    # Serious side effects are flagged for human attention, never diagnosed.
    flagged = bool(body.severity and body.severity >= 7)
    return {"status": "ok", "flagged_for_medical_attention": flagged}
