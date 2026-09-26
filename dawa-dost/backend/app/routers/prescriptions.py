import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Medication, Prescription, User
from app.schemas.schemas import (
    ConfirmPrescriptionRequest,
    ExtractedPrescription,
    MedicationOut,
    PrescriptionOut,
)
from app.services.medication_service import create_medication_with_reminders
from app.services.prescription_parser import parse_frequency
from app.services.sarvam_vision import PrescriptionExtractionError, sarvam_vision_service
from app.utils.current_user import get_current_user
from app.utils.errors import bad_request, extraction_failed, not_found

logger = logging.getLogger("dawa_dost.prescriptions")

router = APIRouter(prefix="/api/prescriptions", tags=["prescriptions"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


@router.get("", response_model=list[PrescriptionOut])
def list_prescriptions(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return (
        db.query(Prescription)
        .filter(Prescription.user_id == user.id)
        .order_by(Prescription.created_at.desc())
        .all()
    )


@router.get("/{prescription_id}", response_model=PrescriptionOut)
def get_prescription(prescription_id: str, db: Session = Depends(get_db)):
    prescription = db.get(Prescription, prescription_id)
    if not prescription:
        raise not_found("Prescription")
    return prescription


@router.post("/upload", response_model=PrescriptionOut)
async def upload_prescription(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise bad_request(
            "Please upload a JPG, PNG, WEBP image or a PDF of the prescription."
        )

    contents = await file.read()
    if not contents:
        raise bad_request("The uploaded file appears to be empty.")

    ext = Path(file.filename or "prescription").suffix or ".jpg"
    stored_name = f"{uuid.uuid4()}{ext}"
    stored_path = UPLOAD_DIR / stored_name
    stored_path.write_bytes(contents)

    prescription = Prescription(
        user_id=user.id,
        image_url=f"/uploads/{stored_name}",
        status="UPLOADED",
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return prescription


@router.post("/{prescription_id}/extract", response_model=PrescriptionOut)
def extract_prescription(prescription_id: str, db: Session = Depends(get_db)):
    prescription = db.get(Prescription, prescription_id)
    if not prescription:
        raise not_found("Prescription")

    if not prescription.image_url:
        raise bad_request("This prescription has no uploaded image to extract from.")

    file_path = UPLOAD_DIR / Path(prescription.image_url).name
    if not file_path.exists():
        raise bad_request("The uploaded prescription file is missing on the server.")

    prescription.status = "PROCESSING"
    db.commit()

    try:
        extracted: ExtractedPrescription = sarvam_vision_service.extract(
            file_bytes=file_path.read_bytes(), filename=file_path.name
        )
    except PrescriptionExtractionError as exc:
        prescription.status = "FAILED"
        db.commit()
        raise extraction_failed(str(exc))

    # Flag ambiguous medication frequencies for the confirmation UI, but
    # never drop or silently reinterpret them.
    medications_payload = []
    for med in extracted.medications:
        parsed = parse_frequency(med.frequency)
        med_dict = med.model_dump()
        med_dict["needs_review"] = parsed.needs_review
        medications_payload.append(med_dict)

    raw_payload = extracted.model_dump()
    raw_payload["medications"] = medications_payload

    prescription.doctor_name = extracted.doctor_name
    # Safety: diagnoses/symptoms are stored exactly as extracted from the
    # document text - never inferred from medicine names.
    prescription.diagnoses = extracted.diagnoses
    prescription.symptoms = extracted.symptoms
    prescription.raw_extraction = raw_payload
    prescription.status = "EXTRACTED"
    db.commit()
    db.refresh(prescription)
    return prescription


@router.post("/{prescription_id}/confirm", response_model=list[MedicationOut])
def confirm_prescription(
    prescription_id: str,
    body: ConfirmPrescriptionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Patient-confirmed medications only. This is the sole path that creates
    active medications + reminder schedules - extraction alone never does."""
    prescription = db.get(Prescription, prescription_id)
    if not prescription:
        raise not_found("Prescription")
    if not body.medications:
        raise bad_request("At least one medication is required to confirm.")

    created: list[Medication] = []
    for item in body.medications:
        medication = create_medication_with_reminders(
            db, user_id=user.id, prescription_id=prescription.id, item=item
        )
        created.append(medication)

    prescription.status = "CONFIRMED"
    db.commit()
    for medication in created:
        db.refresh(medication)
    return created
