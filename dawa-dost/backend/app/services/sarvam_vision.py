"""Prescription extraction via Sarvam Document AI (doc_ai.extract).

This is the only place in the codebase that talks to Sarvam's document
extraction API. Callers get back an ExtractedPrescription; they never see
the raw Sarvam job/polling mechanics.
"""
import json
import time

from sarvamai import SarvamAI

from app.config import get_settings
from app.schemas.schemas import ExtractedPrescription

settings = get_settings()

_EXTRACTION_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {
            "patient_name": {"type": "string", "description": "The patient's full name, if written on the prescription."},
            "doctor_name": {"type": "string", "description": "The prescribing doctor's name, if written on the prescription."},
            "diagnoses": {
                "type": "array",
                "items": {"type": "string", "description": "A single diagnosis exactly as written on the prescription."},
                "description": "Only diagnoses explicitly written on the prescription. Never infer a diagnosis from a medicine name.",
            },
            "symptoms": {
                "type": "array",
                "items": {"type": "string", "description": "A single symptom exactly as written on the prescription."},
                "description": "Only symptoms explicitly written on the prescription.",
            },
            "medications": {
                "type": "array",
                "description": "Every medication line item listed on the prescription.",
                "items": {
                    "type": "object",
                    "description": "One prescribed medication.",
                    "properties": {
                        "medicine_name": {"type": "string", "description": "The name of the medicine."},
                        "strength": {"type": "string", "description": "The medicine's strength, e.g. '500 mg'."},
                        "dose": {"type": "string", "description": "The amount taken per dose, e.g. '1 tablet'."},
                        "frequency": {"type": "string", "description": "How often it is taken, e.g. '1-0-1' or 'twice daily'."},
                        "duration": {"type": "string", "description": "How long the course lasts, e.g. '7 days'."},
                        "food_instruction": {"type": "string", "description": "Whether to take before/after food, if specified."},
                        "special_instruction": {"type": "string", "description": "Any other instruction written for this medicine."},
                    },
                },
            },
        },
    }
)


class PrescriptionExtractionError(Exception):
    pass


class SarvamVisionService:
    """Thin wrapper around Sarvam Document AI's extract job flow."""

    def __init__(self) -> None:
        self._client: SarvamAI | None = None

    def _get_client(self) -> SarvamAI:
        if not settings.sarvam_api_key:
            raise PrescriptionExtractionError(
                "SARVAM_API_KEY is not configured on the server."
            )
        if self._client is None:
            self._client = SarvamAI(api_subscription_key=settings.sarvam_api_key)
        return self._client

    def extract(
        self, file_bytes: bytes, filename: str, poll_timeout_s: float = 60.0
    ) -> ExtractedPrescription:
        """Run Sarvam Document AI extraction on a prescription image/PDF.

        Raises PrescriptionExtractionError on any failure so the caller can
        show a friendly message instead of a blank/guessed result.
        """
        client = self._get_client()

        try:
            job = client.doc_ai.extract(
                file=[(filename, file_bytes)],
                schema=_EXTRACTION_SCHEMA,
                output_format="json",
            )
        except Exception as exc:  # noqa: BLE001 - isolate all Sarvam SDK errors here
            raise PrescriptionExtractionError(f"Sarvam Document AI request failed: {exc}") from exc

        job_id = getattr(job, "job_id", None) or getattr(job, "id", None)
        if not job_id:
            raise PrescriptionExtractionError("Sarvam Document AI did not return a job id.")

        deadline = time.monotonic() + poll_timeout_s
        status = None
        while time.monotonic() < deadline:
            try:
                status_resp = client.doc_ai.get_status(job_id)
            except Exception as exc:  # noqa: BLE001
                raise PrescriptionExtractionError(f"Could not check extraction status: {exc}") from exc
            status = getattr(status_resp, "status", None)
            if status in ("Completed", "COMPLETED", "completed", "SUCCESS", "success"):
                break
            if status in ("Failed", "FAILED", "failed", "ERROR", "error"):
                raise PrescriptionExtractionError("Sarvam Document AI job failed.")
            time.sleep(2)
        else:
            raise PrescriptionExtractionError("Prescription extraction timed out.")

        try:
            results = client.doc_ai.get_results(job_id, format="json")
        except Exception as exc:  # noqa: BLE001
            raise PrescriptionExtractionError(f"Could not fetch extraction results: {exc}") from exc

        data = _coerce_results_to_dict(results)
        if not data:
            raise PrescriptionExtractionError("Sarvam Document AI returned an empty result.")

        try:
            return ExtractedPrescription.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            raise PrescriptionExtractionError(f"Malformed extraction result: {exc}") from exc


def _coerce_results_to_dict(results) -> dict:
    """Sarvam SDK response objects vary by output_format; normalise to dict."""
    if isinstance(results, dict):
        return results
    if hasattr(results, "model_dump"):
        dumped = results.model_dump()
        # extract results are typically wrapped, e.g. {"data": {...}} or
        # {"results": [{"json": {...}}]}
        for key in ("data", "result", "output"):
            if isinstance(dumped.get(key), dict):
                return dumped[key]
        return dumped
    return {}


sarvam_vision_service = SarvamVisionService()
