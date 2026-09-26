"""SQLAlchemy models mirroring supabase/migrations/0001_init.sql.

Primary keys are UUID strings generated in Python so the same models work
against both local SQLite (hackathon default) and Supabase Postgres.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    preferred_language: Mapped[str] = mapped_column(String(16), default="hi-IN")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    doctor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Only ever populated with text explicitly present in the prescription.
    diagnoses: Mapped[list] = mapped_column(JSON, default=list)
    symptoms: Mapped[list] = mapped_column(JSON, default=list)
    raw_extraction: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="UPLOADED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    medications: Mapped[list["Medication"]] = relationship(back_populates="prescription")


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    prescription_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("prescriptions.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    strength: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dose: Mapped[str | None] = mapped_column(String(64), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(128), nullable=True)
    frequency_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    times: Mapped[list] = mapped_column(JSON, default=list)  # ["08:00", "20:00"]
    duration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    start_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    food_instruction: Mapped[str | None] = mapped_column(String(64), nullable=True)
    special_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_sos: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prescription: Mapped[Prescription | None] = relationship(back_populates="medications")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    medication_id: Mapped[str] = mapped_column(String(36), ForeignKey("medications.id"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    call_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("calls.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    reminder_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("reminders.id"), nullable=True
    )
    sarvam_interaction_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AdherenceEvent(Base):
    __tablename__ = "adherence_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    medication_id: Mapped[str] = mapped_column(String(36), ForeignKey("medications.id"))
    call_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("calls.id"), nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SymptomEvent(Base):
    __tablename__ = "symptom_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    call_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("calls.id"), nullable=True)
    symptom: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trend: Mapped[str | None] = mapped_column(String(16), nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="PATIENT_REPORTED")
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SideEffectEvent(Base):
    __tablename__ = "side_effect_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    call_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("calls.id"), nullable=True)
    symptom: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
