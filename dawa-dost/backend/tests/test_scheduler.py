from datetime import datetime, timedelta

from app.models import Medication, Reminder, User
from app.services.scheduler import ReminderScheduler


def _make_user_and_medication(db_session):
    user = User(name="Test Patient", phone="+911111111111")
    db_session.add(user)
    db_session.flush()
    medication = Medication(user_id=user.id, name="TestMed", confirmed=True)
    db_session.add(medication)
    db_session.flush()
    db_session.commit()
    return user, medication


def _bind_scheduler_to_test_session(db_session):
    """The scheduler opens/closes its own SessionLocal() per call; point it
    at the test's in-memory session and stop it from closing that session
    out from under the test."""
    import app.services.scheduler as scheduler_module

    db_session.close = lambda: None
    scheduler_module.SessionLocal = lambda: db_session


def test_schedule_and_cancel_reminder(db_session):
    user, medication = _make_user_and_medication(db_session)
    reminder = Reminder(
        user_id=user.id,
        medication_id=medication.id,
        scheduled_at=datetime.utcnow() + timedelta(hours=1),
        status="PENDING",
    )
    db_session.add(reminder)
    db_session.commit()

    scheduler = ReminderScheduler()
    scheduler.start()
    try:
        scheduler.schedule_reminder(reminder.id, reminder.scheduled_at)
        assert scheduler._scheduler.get_job(scheduler._job_id(reminder.id)) is not None

        _bind_scheduler_to_test_session(db_session)
        scheduler.cancel_reminder(reminder.id)
        assert scheduler._scheduler.get_job(scheduler._job_id(reminder.id)) is None
        db_session.refresh(reminder)
        assert reminder.status == "CANCELLED"
    finally:
        scheduler.shutdown()


def test_snooze_reminder_updates_time_and_status(db_session):
    user, medication = _make_user_and_medication(db_session)
    reminder = Reminder(
        user_id=user.id,
        medication_id=medication.id,
        scheduled_at=datetime.utcnow(),
        status="TRIGGERED",
    )
    db_session.add(reminder)
    db_session.commit()

    _bind_scheduler_to_test_session(db_session)
    scheduler = ReminderScheduler()
    scheduler.start()
    try:
        new_time = scheduler.snooze_reminder(reminder.id, 30)
        db_session.refresh(reminder)
        assert reminder.status == "SNOOZED"
        assert abs((reminder.scheduled_at - new_time).total_seconds()) < 1
        assert new_time > datetime.utcnow() + timedelta(minutes=29)
    finally:
        scheduler.shutdown()


def test_process_due_reminders_triggers_due_jobs(db_session, monkeypatch):
    user, medication = _make_user_and_medication(db_session)
    reminder = Reminder(
        user_id=user.id,
        medication_id=medication.id,
        scheduled_at=datetime.utcnow() - timedelta(minutes=5),
        status="PENDING",
    )
    db_session.add(reminder)
    db_session.commit()

    _bind_scheduler_to_test_session(db_session)
    import app.services.scheduler as scheduler_module

    called = {}

    def fake_trigger_call(phone, agent_variables, metadata):
        called["reminder_id"] = metadata["reminder_id"]
        return "fake-attempt-id"

    monkeypatch.setattr(
        scheduler_module.sarvam_voice_service, "trigger_call", fake_trigger_call
    )

    scheduler = ReminderScheduler()
    processed = scheduler.process_due_reminders()
    assert processed == 1
    assert called["reminder_id"] == reminder.id
    db_session.refresh(reminder)
    assert reminder.status == "TRIGGERED"
