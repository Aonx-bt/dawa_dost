"""Inbound webhook from Sarvam Voice Agents, delivered after each call
completes. Payload shape:
https://docs.sarvam.ai/conversations/api/instant-outbound/webhook-payload

Idempotency: `calls.sarvam_interaction_id` (which stores Sarvam's
`attempt_id` - see note below) is unique. If we've already recorded this
attempt, we return success without creating duplicate adherence/symptom/
side-effect rows - this makes retried webhook deliveries safe.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request
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
    # Sarvam's `interaction_id` can be null (e.g. call never connected), but
    # `attempt_id` is always present and unique per call attempt, so that's
    # our idempotency/correlation key - stored in the sarvam_interaction_id
    # column.
    existing_call = (
        db.query(Call).filter(Call.sarvam_interaction_id == payload.attempt_id).first()
    )
    if existing_call:
        logger.info("Duplicate webhook for attempt %s ignored", payload.attempt_id)
        return {"status": "ok", "duplicate": True, "call_id": existing_call.id}

    reminder_id = payload.reminder_id
    if not reminder_id:
        raise bad_request("Webhook payload is missing reminder_id in webhook_config.metadata.")
    reminder = db.get(Reminder, reminder_id)
    if not reminder:
        raise bad_request(f"Unknown reminder_id: {reminder_id}")

    outcome = payload.to_structured_outcome()

    call = Call(
        user_id=reminder.user_id,
        reminder_id=reminder.id,
        sarvam_interaction_id=payload.attempt_id,
        started_at=None,  # not provided by Sarvam's webhook payload
        ended_at=None,
        duration=int(round(payload.duration)) if payload.duration is not None else None,
        transcript=payload.transcript_text,
        outcome=outcome.model_dump(),
    )
    db.add(call)
    db.flush()

    reminder.call_id = call.id

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
                status="REFUSED" if payload.status not in ("no-answer", "failed", "busy") else "MISSED",
                reason=payload.failure_reason,
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
async def sarvam_webhook(request: Request, db: Session = Depends(get_db)):
    # Sarvam has no documented webhook signature scheme, so we verify via a
    # shared-secret token embedded in the webhook URL's query string
    # ourselves (see SarvamVoiceService.trigger_call / verify_webhook).
    token = request.query_params.get("token")
    if not sarvam_voice_service.verify_webhook(token):
        raise bad_request("Invalid webhook token.")

    try:
        raw = await request.json()
        payload = SarvamWebhookPayload.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        logger.error("Malformed Sarvam webhook payload: %s", exc)
        raise bad_request(f"Malformed webhook payload: {exc}")

    return process_sarvam_outcome(db, payload)
