"""Turns confirmed medications into medication + reminder records."""
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Medication, Reminder
from app.schemas.schemas import MedicationConfirmItem
from app.services.prescription_parser import parse_frequency
from app.services.scheduler import reminder_scheduler

_DURATION_DAYS_MAP = {
    "1 day": 1,
    "3 days": 3,
    "5 days": 5,
    "7 days": 7,
    "10 days": 10,
    "14 days": 14,
}


def _duration_to_days(duration: str | None) -> int:
    if not duration:
        return 5  # sensible default so a schedule can still be generated
    normalized = duration.strip().lower()
    if normalized in _DURATION_DAYS_MAP:
        return _DURATION_DAYS_MAP[normalized]
    digits = "".join(ch for ch in normalized if ch.isdigit())
    if digits:
        return max(1, int(digits))
    return 5


def create_medication_with_reminders(
    db: Session,
    user_id: str,
    prescription_id: str,
    item: MedicationConfirmItem,
) -> Medication:
    """Create one confirmed medication and its recurring reminders.

    SOS/PRN medications get no fixed reminders (patient-triggered only).
    Ambiguous frequencies (needs_review) get the medication saved but with
    no reminders until the patient clarifies via the UI.
    """
    parsed = parse_frequency(item.frequency)

    start = item.start_date or date.today()
    days = _duration_to_days(item.duration)
    end = start + timedelta(days=days - 1)

    medication = Medication(
        user_id=user_id,
        prescription_id=prescription_id,
        name=item.medicine_name,
        strength=item.strength,
        dose=item.dose,
        frequency=item.frequency,
        frequency_code=parsed.frequency_code,
        times=parsed.times,
        duration=item.duration,
        start_date=start,
        end_date=end,
        food_instruction=item.food_instruction,
        special_instruction=item.special_instruction,
        is_sos=parsed.is_sos,
        needs_review=parsed.needs_review,
        confirmed=True,
    )
    db.add(medication)
    db.flush()  # assign medication.id

    if not parsed.is_sos and not parsed.needs_review and parsed.times:
        for day_offset in range(days):
            day = start + timedelta(days=day_offset)
            for time_str in parsed.times:
                hour, minute = (int(part) for part in time_str.split(":"))
                scheduled_at = datetime.combine(day, datetime.min.time()).replace(
                    hour=hour, minute=minute
                )
                if scheduled_at < datetime.utcnow() - timedelta(minutes=5):
                    continue  # don't backfill reminders for times already past
                reminder = Reminder(
                    user_id=user_id,
                    medication_id=medication.id,
                    scheduled_at=scheduled_at,
                    status="PENDING",
                )
                db.add(reminder)
                db.flush()
                reminder_scheduler.schedule_reminder(reminder.id, scheduled_at)

    return medication
