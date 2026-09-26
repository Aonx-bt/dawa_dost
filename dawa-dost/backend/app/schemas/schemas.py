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


class SarvamChannelInfo(BaseModel):
    channel_type: str
    channel_provider: str
    agent_phone_number: str


class SarvamWebhookConfigEcho(BaseModel):
    url: str
    metadata: dict[str, Any] | None = None


class SarvamTranscriptTurn(BaseModel):
    role: str
    en_text: str


class SarvamWebhookPayload(BaseModel):
    """Real inbound webhook payload from Sarvam Voice Agents after a call
    finishes. Shape per:
    https://docs.sarvam.ai/conversations/api/instant-outbound/webhook-payload

    Sarvam gives us no structured "outcome" object directly - the agent is
    expected to set `final_agent_variables` during the call (medication_taken,
    snooze_requested, symptom_name, ...), which we parse via
    to_structured_outcome(). We correlate the call back to our reminder via
    `webhook_config.metadata.reminder_id`, which we set ourselves when
    triggering the call (see SarvamVoiceService.trigger_call).
    """

    attempt_id: str
    status: str
    channel_info: SarvamChannelInfo | None = None
    duration: float | None = None
    interaction_id: str | None = None
    failure_reason: str | None = None
    final_agent_variables: dict[str, Any] | None = None
    webhook_config: SarvamWebhookConfigEcho | None = None
    interaction_transcript: list[SarvamTranscriptTurn] | None = None

    @property
    def reminder_id(self) -> str | None:
        if self.webhook_config and self.webhook_config.metadata:
            value = self.webhook_config.metadata.get("reminder_id")
            return str(value) if value is not None else None
        return None

    @property
    def transcript_text(self) -> str | None:
        if not self.interaction_transcript:
            return None
        return "\n".join(f"{t.role}: {t.en_text}" for t in self.interaction_transcript)

    def to_structured_outcome(self) -> StructuredCallOutcome:
        """Best-effort parse of the agent's final_agent_variables into our
        internal StructuredCallOutcome shape. The Samvaad agent must be
        configured to set these variable names during the call."""
        variables = self.final_agent_variables or {}

        def as_bool(key: str) -> bool:
            value = variables.get(key)
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in ("true", "1", "yes")
            return False

        def as_int(key: str) -> int | None:
            value = variables.get(key)
            try:
                return int(value) if value is not None else None
            except (ValueError, TypeError):
                return None

        call_failed = self.status in ("no-answer", "failed", "busy", "declined")

        return StructuredCallOutcome(
            medication_taken=as_bool("medication_taken"),
            snooze_requested=as_bool("snooze_requested"),
            snooze_minutes=as_int("snooze_minutes") or 30,
            symptom_reported=as_bool("symptom_reported"),
            symptom_name=variables.get("symptom_name"),
            symptom_severity=as_int("symptom_severity"),
            symptom_trend=variables.get("symptom_trend"),
            side_effect_reported=as_bool("side_effect_reported"),
            side_effect_name=variables.get("side_effect_name"),
            side_effect_severity=as_int("side_effect_severity"),
            refused=call_failed or as_bool("refused"),
        )


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


# ---------------------------------------------------------------------------
# Medicine insights (informational only - see app/services/medicine_reference.py)
# ---------------------------------------------------------------------------


class MedicineInsightsRequest(BaseModel):
    medicine_names: list[str] = Field(min_length=1, max_length=20)


class MedicinePricing(BaseModel):
    branded_price_inr: float | None
    generic_name: str | None
    generic_price_inr: float | None
    cheaper_generic_available: bool
    source: str | None


class MedicineInsight(BaseModel):
    medicine_name: str
    description: str
    drug_class: str
    common_uses: list[str]
    pricing: MedicinePricing


class InteractionFlag(BaseModel):
    medicines: list[str]
    note: str
    recommendation: str


class MedicineInsightsResponse(BaseModel):
    medicines: list[MedicineInsight]
    interaction_flags: list[InteractionFlag]
    disclaimer: str
