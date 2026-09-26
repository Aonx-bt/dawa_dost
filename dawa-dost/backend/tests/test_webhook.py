from datetime import datetime

from app.models import Call, Medication, Reminder, User


def _seed_reminder(db_session):
    user = User(name="Webhook Test", phone="+913333333333")
    db_session.add(user)
    db_session.flush()
    medication = Medication(user_id=user.id, name="TestMed", confirmed=True)
    db_session.add(medication)
    db_session.flush()
    reminder = Reminder(
        user_id=user.id,
        medication_id=medication.id,
        scheduled_at=datetime.utcnow(),
        status="TRIGGERED",
    )
    db_session.add(reminder)
    db_session.commit()
    return user, medication, reminder


def _sarvam_payload(attempt_id: str, reminder_id: str, **agent_variables):
    return {
        "attempt_id": attempt_id,
        "status": "connected",
        "duration": 42.5,
        "interaction_id": f"{attempt_id}-interaction",
        "final_agent_variables": agent_variables,
        "webhook_config": {"url": "https://example.com/webhook", "metadata": {"reminder_id": reminder_id}},
        "interaction_transcript": [{"role": "agent", "en_text": "Did you take your medicine?"}],
    }


def test_valid_webhook_creates_call_and_adherence(client, db_session):
    user, medication, reminder = _seed_reminder(db_session)

    resp = client.post(
        "/api/webhooks/sarvam",
        json=_sarvam_payload("webhook-valid-1", reminder.id, medication_taken=True),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    calls = db_session.query(Call).filter(Call.sarvam_interaction_id == "webhook-valid-1").all()
    assert len(calls) == 1


def test_duplicate_webhook_is_idempotent(client, db_session):
    user, medication, reminder = _seed_reminder(db_session)
    payload = _sarvam_payload("webhook-dup-1", reminder.id, medication_taken=True)
    first = client.post("/api/webhooks/sarvam", json=payload)
    second = client.post("/api/webhooks/sarvam", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json().get("duplicate") is True

    calls = db_session.query(Call).filter(Call.sarvam_interaction_id == "webhook-dup-1").all()
    assert len(calls) == 1


def test_malformed_webhook_returns_400(client):
    resp = client.post("/api/webhooks/sarvam", json={"not_a_valid_field": True})
    assert resp.status_code == 400
