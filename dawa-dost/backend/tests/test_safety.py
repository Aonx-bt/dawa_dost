"""Safety-critical rules (see spec section 20)."""
from app.schemas.schemas import ExtractedPrescription
from app.services.prescription_parser import parse_frequency


def test_diagnosis_is_never_inferred_from_medication_name():
    """Extraction schema has no mechanism to derive diagnoses from medicine
    names - diagnoses/symptoms are independent fields populated only from
    document text. This test locks that shape in place."""
    extracted = ExtractedPrescription(
        medications=[{"medicine_name": "Amoxicillin", "strength": "500 mg"}]
    )
    # No diagnoses/symptoms were provided alongside the medicine - none
    # should be silently populated.
    assert extracted.diagnoses == []
    assert extracted.symptoms == []


def test_ambiguous_frequency_requires_confirmation_not_a_guess():
    for ambiguous in ("BD", "TDS", "QDS", "twice a week maybe"):
        result = parse_frequency(ambiguous)
        assert result.needs_review is True
        assert result.times == [], f"{ambiguous} must not produce a guessed schedule"


def test_sos_never_produces_recurring_schedule():
    result = parse_frequency("SOS")
    assert result.is_sos is True
    assert result.times == []
