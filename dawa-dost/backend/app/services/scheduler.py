"""Reminder scheduling abstraction.

For the hackathon this runs APScheduler in-process inside FastAPI. The public
surface (schedule_reminder / cancel_reminder / snooze_reminder /
process_due_reminders) is intentionally small so a production deployment can
later swap in a durable scheduler (e.g. a managed cron + queue) without
touching callers.
"""
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from app.database import SessionLocal
from app.models import Medication, Reminder, User
from app.services.sarvam_voice import VoiceCallError, sarvam_voice_service

logger = logging.getLogger("dawa_dost.scheduler")


class ReminderScheduler:
    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler()
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._scheduler.start()
            self._started = True

    def shutdown(self) -> None:
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False

    @staticmethod
    def _job_id(reminder_id: str) -> str:
        return f"reminder:{reminder_id}"

    def schedule_reminder(self, reminder_id: str, scheduled_at: datetime) -> None:
        """(Re)schedule a job that fires the voice call at scheduled_at."""
        job_id = self._job_id(reminder_id)
        self._scheduler.add_job(
            self._fire,
            trigger=DateTrigger(run_date=scheduled_at),
            args=[reminder_id],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600,
        )

    def cancel_reminder(self, reminder_id: str) -> None:
        job_id = self._job_id(reminder_id)
        try:
            self._scheduler.remove_job(job_id)
        except Exception:  # noqa: BLE001 - job may not exist, that's fine
            pass
        db = SessionLocal()
        try:
            reminder = db.get(Reminder, reminder_id)
            if reminder and reminder.status in ("PENDING", "SNOOZED"):
                reminder.status = "CANCELLED"
                reminder.updated_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()

    def snooze_reminder(self, reminder_id: str, minutes: int) -> datetime:
        db = SessionLocal()
        try:
            reminder = db.get(Reminder, reminder_id)
            if not reminder:
                raise ValueError(f"Reminder {reminder_id} not found")
            new_time = datetime.utcnow() + timedelta(minutes=minutes)
            reminder.scheduled_at = new_time
            reminder.status = "SNOOZED"
            reminder.updated_at = datetime.utcnow()
            db.commit()
        finally:
            db.close()
        self.schedule_reminder(reminder_id, new_time)
        return new_time

    def _fire(self, reminder_id: str) -> None:
        """Job callback: trigger the Samvaad call for a due reminder."""
        db = SessionLocal()
        try:
            reminder = db.get(Reminder, reminder_id)
            if not reminder or reminder.status not in ("PENDING", "SNOOZED"):
                return
            medication = db.get(Medication, reminder.medication_id)
            user = db.get(User, reminder.user_id)
            if not medication or not user:
                logger.error("Reminder %s missing medication/user", reminder_id)
                return

            agent_variables = {
                "patient_name": user.name,
                "medication_name": medication.name,
                "dose": medication.dose or "",
                "food_instruction": medication.food_instruction or "",
                "scheduled_time": reminder.scheduled_at.strftime("%H:%M"),
            }
            metadata = {"reminder_id": reminder.id, "medication_id": medication.id, "user_id": user.id}
            try:
                attempt_id = sarvam_voice_service.trigger_call(user.phone, agent_variables, metadata)
                reminder.status = "TRIGGERED"
                reminder.updated_at = datetime.utcnow()
                db.commit()
                logger.info("Triggered Samvaad call %s for reminder %s", attempt_id, reminder_id)
            except VoiceCallError as exc:
                logger.error("Voice call failed for reminder %s: %s", reminder_id, exc)
                # Leave reminder PENDING so it can be retried/triggered manually
                # (e.g. via Demo Mode's "Call me now").
        finally:
            db.close()

    def process_due_reminders(self) -> int:
        """Fallback sweep for reminders whose scheduled time has passed but
        whose APScheduler job never fired (e.g. after a server restart)."""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            due = (
                db.query(Reminder)
                .filter(Reminder.status.in_(["PENDING", "SNOOZED"]))
                .filter(Reminder.scheduled_at <= now)
                .all()
            )
            ids = [r.id for r in due]
        finally:
            db.close()
        for reminder_id in ids:
            self._fire(reminder_id)
        return len(ids)


reminder_scheduler = ReminderScheduler()
