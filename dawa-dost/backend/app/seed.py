"""Seed demo data so the dashboard looks populated immediately (see spec #25).

Idempotent: running it twice does not duplicate the demo patient.
"""
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import AdherenceEvent, Call, Medication, Prescription, Reminder, SymptomEvent, User
from app.utils.current_user import DEMO_LANGUAGE, DEMO_NAME, DEMO_PHONE


def seed(db: Session) -> None:
    existing = db.query(User).filter(User.phone == DEMO_PHONE).first()
    if existing:
        return

    user = User(name=DEMO_NAME, phone=DEMO_PHONE, preferred_language=DEMO_LANGUAGE)
    db.add(user)
    db.flush()

    prescription = Prescription(
        user_id=user.id,
        doctor_name="Dr. Mehta",
        diagnoses=["Viral fever"],
        symptoms=["Fever", "Body ache"],
        raw_extraction=None,
        status="CONFIRMED",
    )
    db.add(prescription)
    db.flush()

    today = date.today()

    crocin = Medication(
        user_id=user.id,
        prescription_id=prescription.id,
        name="Crocin",
        strength="500 mg",
        dose="1 tablet",
        frequency="1-0-1",
        frequency_code="1-0-1",
        times=["08:00", "20:00"],
        duration="5 days",
        start_date=today,
        end_date=today + timedelta(days=4),
        food_instruction="After food",
        confirmed=True,
    )
    azithro = Medication(
        user_id=user.id,
        prescription_id=prescription.id,
        name="Azithromycin",
        strength="500 mg",
        dose="1 tablet",
        frequency="0-1-0",
        frequency_code="0-1-0",
        times=["14:00"],
        duration="3 days",
        start_date=today,
        end_date=today + timedelta(days=2),
        food_instruction="After food",
        confirmed=True,
    )
    db.add_all([crocin, azithro])
    db.flush()

    now = datetime.utcnow()
    morning_reminder = Reminder(
        user_id=user.id,
        medication_id=crocin.id,
        scheduled_at=datetime.combine(today, datetime.min.time()).replace(hour=8),
        status="COMPLETED",
    )
    afternoon_reminder = Reminder(
        user_id=user.id,
        medication_id=azithro.id,
        scheduled_at=datetime.combine(today, datetime.min.time()).replace(hour=14),
        status="COMPLETED",
    )
    evening_reminder = Reminder(
        user_id=user.id,
        medication_id=crocin.id,
        scheduled_at=datetime.combine(today, datetime.min.time()).replace(hour=20),
        status="PENDING",
    )
    db.add_all([morning_reminder, afternoon_reminder, evening_reminder])
    db.flush()

    call_1 = Call(
        user_id=user.id,
        reminder_id=morning_reminder.id,
        sarvam_interaction_id="seed-call-1",
        started_at=now - timedelta(hours=6),
        ended_at=now - timedelta(hours=6) + timedelta(seconds=40),
        duration=40,
        transcript="Namaste Rina ji, Crocin ki subah ki dose ka time ho gaya hai...",
        outcome={"medication_taken": True},
    )
    call_2 = Call(
        user_id=user.id,
        reminder_id=afternoon_reminder.id,
        sarvam_interaction_id="seed-call-2",
        started_at=now - timedelta(hours=1),
        ended_at=now - timedelta(hours=1) + timedelta(seconds=35),
        duration=35,
        transcript="Namaste Rina ji, Azithromycin ki dopahar ki dose ka time ho gaya hai...",
        outcome={"medication_taken": True, "symptom_reported": True, "symptom_name": "fever"},
    )
    db.add_all([call_1, call_2])
    db.flush()

    morning_reminder.call_id = call_1.id
    afternoon_reminder.call_id = call_2.id

    db.add_all(
        [
            AdherenceEvent(
                user_id=user.id,
                medication_id=crocin.id,
                call_id=call_1.id,
                scheduled_at=morning_reminder.scheduled_at,
                status="TAKEN",
            ),
            AdherenceEvent(
                user_id=user.id,
                medication_id=azithro.id,
                call_id=call_2.id,
                scheduled_at=afternoon_reminder.scheduled_at,
                status="TAKEN",
            ),
        ]
    )

    db.add_all(
        [
            SymptomEvent(
                user_id=user.id,
                call_id=call_1.id,
                symptom="fever",
                severity=8,
                trend="same",
                reported_at=now - timedelta(days=2),
            ),
            SymptomEvent(
                user_id=user.id,
                call_id=call_1.id,
                symptom="fever",
                severity=6,
                trend="improving",
                reported_at=now - timedelta(days=1),
            ),
            SymptomEvent(
                user_id=user.id,
                call_id=call_2.id,
                symptom="fever",
                severity=4,
                trend="improving",
                reported_at=now,
            ),
        ]
    )

    db.commit()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
