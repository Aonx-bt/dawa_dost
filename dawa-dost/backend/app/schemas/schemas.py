"""Pydantic request/response schemas."""
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


class UserOut(BaseModel):
    id: str
    name: str
    phone: str
    preferred_language: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Prescriptions
# ---------------------------------------------------------------------------


class ExtractedMedication(BaseModel):
    medicine_name: str
    strength: str | None = None
    dose: str | None = None
    frequency: str | None = None
    duration: str | None = None
    food_instruction: str | None = None
    special_instruction: str | None = None
    needs_review: bool = False


class ExtractedPrescription(BaseModel):
    """The target structure produced by Sarvam Vision / Document AI."""

    patient_name: str | None = None
    doctor_name: str | None = None
    diagnoses: list[str] = Field(default_factory=list)
    symptoms: list[str] = Field(default_factory=list)
    medications: list[ExtractedMedication] = Field(default_factory=list)


class PrescriptionOut(BaseModel):
    id: str
    user_id: str
    image_url: str | None
    doctor_name: str | None
    diagnoses: list[str]
    symptoms: list[str]
    raw_extraction: dict[str, Any] | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MedicationConfirmItem(BaseModel):
    """A single medication row as edited/confirmed by the patient."""

    medicine_name: str
    strength: str | None = None
    dose: str | None = None
    frequency: str | None = None
    duration: str | None = None
    food_instruction: str | None = None
    special_instruction: str | None = None
    start_date: date | None = None


class ConfirmPrescriptionRequest(BaseModel):
    medications: list[MedicationConfirmItem]


# ---------------------------------------------------------------------------
# Medications
# ---------------------------------------------------------------------------


class MedicationOut(BaseModel):
    id: str
    user_id: str
    prescription_id: str | None
    name: str
    strength: str | None
    dose: str | None
    frequency: str | None
    frequency_code: str | None
    times: list[str]
    duration: str | None
    start_date: date | None
    end_date: date | None
    food_instruction: str | None
    special_instruction: str | None
    is_sos: bool
    needs_review: bool
    confirmed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Reminders / Calls
# ---------------------------------------------------------------------------


class ReminderOut(BaseModel):
    id: str
    user_id: str
    medication_id: str
    scheduled_at: datetime
    status: str
    call_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CallOut(BaseModel):
    id: str
    user_id: str
    reminder_id: str | None
    sarvam_interaction_id: str | None
    started_at: datetime | None
    ended_at: datetime | None
    duration: int | None
    transcript: str | None
    outcome: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Voice / Sarvam Samvaad integration
# ---------------------------------------------------------------------------


class TriggerCallRequest(BaseModel):
    reminder_id: str


class VoiceContextRequest(BaseModel):
    reminder_id: str


class MedicationTakenRequest(BaseModel):
    reminder_id: str
    medication_id: str


class MedicationSnoozeRequest(BaseModel):
    reminder_id: str
    minutes: int = 30


class SymptomReportRequest(BaseModel):
    user_id: str
    call_id: str | None = None
    symptom: str
    severity: int | None = Field(default=None, ge=0, le=10)
    trend: Literal["improving", "worsening", "same", "unknown"] | None = None


class SideEffectReportRequest(BaseModel):
    user_id: str
    call_id: str | None = None
    symptom: str
    severity: int | None = Field(default=None, ge=0, le=10)


class StructuredCallOutcome(BaseModel):
    """What the Samvaad agent should send back after a call completes."""

    medication_taken: bool = False
    snooze_requested: bool = False
    snooze_minutes: int = 30
    symptom_reported: bool = False
    symptom_name: str | None = None
    symptom_severity: int | None = None
    symptom_trend: Literal["improving", "worsening", "same", "unknown"] | None = None
    side_effect_reported: bool = False
    side_effect_name: str | None = None
    side_effect_severity: int | None = None
    refused: bool = False


class SarvamWebhookPayload(BaseModel):
    """Inbound webhook payload from Sarvam Samvaad after a call finishes."""

    interaction_id: str
    reminder_id: str | None = None
    call_id: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration: int | None = None
    transcript: str | None = None
    outcome: StructuredCallOutcome = Field(default_factory=StructuredCallOutcome)


# ---------------------------------------------------------------------------
# Dashboard / progress
# ---------------------------------------------------------------------------


class TodayDoseOut(BaseModel):
    reminder_id: str
    medication_name: str
    dose: str | None
    scheduled_at: datetime
    status: str


class SymptomTrendPoint(BaseModel):
    reported_at: datetime
    severity: int | None
    trend: str | None


class SymptomTrendOut(BaseModel):
    symptom: str
    source: str = "PATIENT_REPORTED"
    points: list[SymptomTrendPoint]


class DashboardOut(BaseModel):
    user: UserOut
    adherence_percent: float
    doses_completed_today: int
    doses_total_today: int
    today: list[TodayDoseOut]
    symptom_trends: list[SymptomTrendOut]
    recent_calls: list[CallOut]
