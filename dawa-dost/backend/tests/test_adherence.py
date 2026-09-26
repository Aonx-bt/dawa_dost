from datetime import datetime

from app.models import Medication, Reminder, User


def _seed_reminder(db_session, status="PENDING"):
    user = User(name="Adherence Test", phone="+912222222222")
    db_session.add(user)
    db_session.flush()
    medication = Medication(user_id=user.id, name="TestMed", confirmed=True)
    db_session.add(medication)
    db_session.flush()
    reminder = Reminder(
        user_id=user.id,
        medication_id=medication.id,
        scheduled_at=datetime.utcnow(),
        status=status,
    )
    db_session.add(reminder)
    db_session.commit()
    return user, medication, reminder


def test_mark_taken_creates_adherence_event_and_completes_reminder(client, db_session):
    user, medication, reminder = _seed_reminder(db_session)

    resp = client.post(
        "/api/voice/medication/taken",
        json={"reminder_id": reminder.id, "medication_id": medication.id},
    )
    assert resp.status_code == 200

    db_session.refresh(reminder)
    assert reminder.status == "COMPLETED"


def test_snooze_creates_snoozed_event_and_reschedules(client, db_session):
    user, medication, reminder = _seed_reminder(db_session)

    resp = client.post(
        "/api/voice/medication/snooze",
        json={"reminder_id": reminder.id, "minutes": 15},
    )
    assert resp.status_code == 200

    db_session.refresh(reminder)
    assert reminder.status == "SNOOZED"


def test_missed_via_webhook_refused_outcome(client, db_session):
    user, medication, reminder = _seed_reminder(db_session, status="TRIGGERED")

    resp = client.post(
        "/api/webhooks/sarvam",
        json={
            "interaction_id": "test-missed-1",
            "reminder_id": reminder.id,
            "outcome": {"refused": True},
        },
    )
    assert resp.status_code == 200
    db_session.refresh(reminder)
    assert reminder.status == "MISSED"
