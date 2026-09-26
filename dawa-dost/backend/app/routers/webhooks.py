"""Inbound webhook from Sarvam Samvaad, delivered after each call completes.

Idempotency: `calls.sarvam_interaction_id` is unique. If we've already
recorded this interaction, we return success without creating duplicate
adherence/symptom/side-effect rows - this makes retried webhook deliveries
safe.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AdherenceEvent, Call, Reminder, SideEffectEvent, SymptomEvent
from app.schemas.schemas import SarvamWebhookPayload
from app.services.scheduler import reminder_scheduler
from app.services.sarvam_voice import sarvam_voice_service
from app.utils.errors import bad_request

logger = logging.getLogger("dawa_dost.webhooks")

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def process_sarvam_outcome(db: Session, payload: SarvamWebhookPayload) -> dict:
    """Shared logic for a completed Samvaad interaction.

    Used by both the real /api/webhooks/sarvam endpoint and Demo Mode's
    simulate-outcome endpoint, so the two paths behave identically.
    """
    existing_call = (
        db.query(Call).filter(Call.sarvam_interaction_id == payload.interaction_id).first()
    )
    if existing_call:
        logger.info("Duplicate webhook for interaction %s ignored", payload.interaction_id)
        return {"status": "ok", "duplicate": True, "call_id": existing_call.id}

    if not payload.reminder_id:
        raise bad_request("Webhook payload is missing reminder_id.")
    reminder = db.get(Reminder, payload.reminder_id)
    if not reminder:
        raise bad_request(f"Unknown reminder_id: {payload.reminder_id}")

    call = Call(
        user_id=reminder.user_id,
        reminder_id=reminder.id,
        sarvam_interaction_id=payload.interaction_id,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        duration=payload.duration,
        transcript=payload.transcript,
        outcome=payload.outcome.model_dump(),
    )
    db.add(call)
    db.flush()

    reminder.call_id = call.id
    outcome = payload.outcome

    if outcome.medication_taken:
        db.add(
            AdherenceEvent(
                user_id=reminder.user_id,
                medication_id=reminder.medication_id,
                call_id=call.id,
                scheduled_at=reminder.scheduled_at,
                status="TAKEN",
            )
        )
        reminder.status = "COMPLETED"
    elif outcome.snooze_requested:
        reminder_scheduler.snooze_reminder(reminder.id, outcome.snooze_minutes)
        db.add(
            AdherenceEvent(
                user_id=reminder.user_id,
                medication_id=reminder.medication_id,
                call_id=call.id,
                scheduled_at=reminder.scheduled_at,
                status="SNOOZED",
                reason=f"Snoozed {outcome.snooze_minutes} minutes",
            )
        )
    elif outcome.refused:
        db.add(
            AdherenceEvent(
                user_id=reminder.user_id,
                medication_id=reminder.medication_id,
                call_id=call.id,
                scheduled_at=reminder.scheduled_at,
                status="REFUSED",
            )
        )
        reminder.status = "MISSED"
    else:
        db.add(
            AdherenceEvent(
                user_id=reminder.user_id,
                medication_id=reminder.medication_id,
                call_id=call.id,
                scheduled_at=reminder.scheduled_at,
                status="UNKNOWN",
            )
        )

    if outcome.symptom_reported and outcome.symptom_name:
        db.add(
            SymptomEvent(
                user_id=reminder.user_id,
                call_id=call.id,
                symptom=outcome.symptom_name,
                severity=outcome.symptom_severity,
                trend=outcome.symptom_trend,
                source="PATIENT_REPORTED",
            )
        )

    if outcome.side_effect_reported and outcome.side_effect_name:
        db.add(
            SideEffectEvent(
                user_id=reminder.user_id,
                call_id=call.id,
                symptom=outcome.side_effect_name,
                severity=outcome.side_effect_severity,
            )
        )

    reminder.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "ok", "call_id": call.id}


@router.post("/sarvam")
async def sarvam_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_sarvam_signature: str | None = Header(default=None),
):
    if not sarvam_voice_service.verify_webhook(x_sarvam_signature):
        raise bad_request("Invalid webhook signature.")

    try:
        raw = await request.json()
        payload = SarvamWebhookPayload.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        logger.error("Malformed Sarvam webhook payload: %s", exc)
        raise bad_request(f"Malformed webhook payload: {exc}")

    return process_sarvam_outcome(db, payload)
