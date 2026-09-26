"""Demo Mode endpoints for the hackathon.

The real path is: confirm prescription -> reminders -> Samvaad call ->
webhook. When a live phone call isn't available (e.g. judging offline),
`/simulate-outcome` lets us post the same structured outcome a real call
would produce, going through the exact same processing logic as a genuine
Sarvam webhook.
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Reminder, User
from app.routers.webhooks import process_sarvam_outcome
from app.schemas.schemas import SarvamTranscriptTurn, SarvamWebhookConfigEcho, SarvamWebhookPayload, StructuredCallOutcome
from app.utils.current_user import get_current_user
from app.utils.errors import not_found

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/user")
def demo_user(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "phone": user.phone}


class SimulateOutcomeRequest(BaseModel):
    reminder_id: str
    outcome: StructuredCallOutcome = StructuredCallOutcome(medication_taken=True)


@router.post("/simulate-outcome")
def simulate_outcome(body: SimulateOutcomeRequest, db: Session = Depends(get_db)):
    reminder = db.get(Reminder, body.reminder_id)
    if not reminder:
        raise not_found("Reminder")

    now = datetime.utcnow()
    outcome = body.outcome
    # Mirror the real webhook shape: our outcome flags travel as
    # final_agent_variables (what the real Samvaad agent would set), and
    # reminder_id travels via webhook_config.metadata (what we set when
    # triggering the call) - see SarvamWebhookPayload.to_structured_outcome
    # and .reminder_id.
    payload = SarvamWebhookPayload(
        attempt_id=f"demo-{reminder.id}-{int(now.timestamp())}",
        status="connected",
        duration=45.0,
        interaction_id=f"demo-{reminder.id}-{int(now.timestamp())}",
        final_agent_variables={
            "medication_taken": outcome.medication_taken,
            "snooze_requested": outcome.snooze_requested,
            "snooze_minutes": outcome.snooze_minutes,
            "symptom_reported": outcome.symptom_reported,
            "symptom_name": outcome.symptom_name,
            "symptom_severity": outcome.symptom_severity,
            "symptom_trend": outcome.symptom_trend,
            "side_effect_reported": outcome.side_effect_reported,
            "side_effect_name": outcome.side_effect_name,
            "side_effect_severity": outcome.side_effect_severity,
            "refused": outcome.refused,
        },
        webhook_config=SarvamWebhookConfigEcho(
            url="demo://simulated", metadata={"reminder_id": reminder.id}
        ),
        interaction_transcript=[
            SarvamTranscriptTurn(
                role="system", en_text="[Demo Mode] Simulated call - no real phone call was placed."
            )
        ],
    )
    return process_sarvam_outcome(db, payload)
