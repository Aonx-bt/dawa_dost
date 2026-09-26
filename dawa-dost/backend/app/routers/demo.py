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
from app.schemas.schemas import SarvamWebhookPayload, StructuredCallOutcome
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
    payload = SarvamWebhookPayload(
        interaction_id=f"demo-{reminder.id}-{int(now.timestamp())}",
        reminder_id=reminder.id,
        started_at=now,
        ended_at=now,
        duration=45,
        transcript="[Demo Mode] Simulated call - no real phone call was placed.",
        outcome=body.outcome,
    )
    return process_sarvam_outcome(db, payload)
