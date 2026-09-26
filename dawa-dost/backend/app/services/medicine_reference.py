"""Medicine reference data: what a medicine is for, a cheaper generic
equivalent, and known interaction pairs to flag for the patient to confirm
with their doctor/pharmacist.

IMPORTANT - safety scope: this module never decides a prescription is
"wrong," never recommends stopping or substituting a medication, and never
infers a diagnosis. Interaction flags are informational prompts to consult
a doctor/pharmacist - nothing here changes what gets scheduled or dispensed.

All data below is DUMMY/DEMO data for the hackathon build (see product
spec: "use dummy data for this"). It is not sourced from a real drug
database or the actual Jan Aushadhi price list, and must not be treated as
clinically validated before any real deployment.
"""
from dataclasses import dataclass, field


@dataclass
class MedicineInfo:
    description: str
    drug_class: str
    common_uses: list[str] = field(default_factory=list)
    generic_name: str = ""
    branded_price_inr: float = 0.0
    generic_price_inr: float = 0.0
    price_source: str = "Jan Aushadhi generic price list (demo data)"


# Keyed by lowercase medicine name. Demo dataset covering common OTC/
# prescription medicines, including the ones used in this app's seed data.
_MEDICINE_INFO: dict[str, MedicineInfo] = {
    "crocin": MedicineInfo(
        description="A pain reliever and fever reducer, commonly used for headaches, body ache and fever.",
        drug_class="Analgesic / antipyretic (paracetamol)",
        common_uses=["fever", "headache", "body ache", "mild pain"],
        generic_name="Paracetamol",
        branded_price_inr=32.0,
        generic_price_inr=8.0,
    ),
    "paracetamol": MedicineInfo(
        description="A pain reliever and fever reducer, commonly used for headaches, body ache and fever.",
        drug_class="Analgesic / antipyretic",
        common_uses=["fever", "headache", "body ache", "mild pain"],
        generic_name="Paracetamol",
        branded_price_inr=25.0,
        generic_price_inr=8.0,
    ),
    "azithromycin": MedicineInfo(
        description="An antibiotic used to treat bacterial infections of the respiratory tract, skin and ear.",
        drug_class="Macrolide antibiotic",
        common_uses=["bacterial infection", "respiratory infection"],
        generic_name="Azithromycin",
        branded_price_inr=118.0,
        generic_price_inr=42.0,
    ),
    "amoxicillin": MedicineInfo(
        description="A penicillin-type antibiotic used to treat a wide range of bacterial infections.",
        drug_class="Penicillin antibiotic",
        common_uses=["bacterial infection", "ear infection", "throat infection"],
        generic_name="Amoxicillin",
        branded_price_inr=95.0,
        generic_price_inr=30.0,
    ),
    "ibuprofen": MedicineInfo(
        description="A pain reliever that also reduces inflammation and fever.",
        drug_class="NSAID (non-steroidal anti-inflammatory drug)",
        common_uses=["pain", "inflammation", "fever"],
        generic_name="Ibuprofen",
        branded_price_inr=45.0,
        generic_price_inr=15.0,
    ),
    "cetrizine": MedicineInfo(
        description="An antihistamine used to relieve allergy symptoms like sneezing, itching and runny nose.",
        drug_class="Antihistamine",
        common_uses=["allergy", "itching", "runny nose"],
        generic_name="Cetirizine",
        branded_price_inr=28.0,
        generic_price_inr=9.0,
    ),
    "cetirizine": MedicineInfo(
        description="An antihistamine used to relieve allergy symptoms like sneezing, itching and runny nose.",
        drug_class="Antihistamine",
        common_uses=["allergy", "itching", "runny nose"],
        generic_name="Cetirizine",
        branded_price_inr=28.0,
        generic_price_inr=9.0,
    ),
    "omeprazole": MedicineInfo(
        description="Reduces stomach acid production, used for acidity, heartburn and stomach ulcers.",
        drug_class="Proton pump inhibitor",
        common_uses=["acidity", "heartburn", "stomach ulcer"],
        generic_name="Omeprazole",
        branded_price_inr=60.0,
        generic_price_inr=18.0,
    ),
    "metformin": MedicineInfo(
        description="Helps control blood sugar levels in type 2 diabetes.",
        drug_class="Biguanide (anti-diabetic)",
        common_uses=["type 2 diabetes", "blood sugar control"],
        generic_name="Metformin",
        branded_price_inr=40.0,
        generic_price_inr=12.0,
    ),
    "aspirin": MedicineInfo(
        description="A pain reliever that also thins the blood; sometimes used to reduce heart attack/stroke risk.",
        drug_class="NSAID / antiplatelet",
        common_uses=["pain", "fever", "blood thinning"],
        generic_name="Aspirin",
        branded_price_inr=20.0,
        generic_price_inr=6.0,
    ),
}

_GENERIC_DEFAULT = MedicineInfo(
    description="We don't have detailed information on this medicine in our reference list yet. Please ask your pharmacist or doctor about what it's for.",
    drug_class="Unknown",
    common_uses=[],
)

# Demo interaction pairs (lowercase names, order-independent). Real clinical
# interaction checking requires a licensed drug-interaction database - this
# is a small illustrative set for the hackathon build only.
_INTERACTION_PAIRS: list[tuple[str, str, str]] = [
    ("ibuprofen", "aspirin", "Taking two NSAIDs together can increase the risk of stomach irritation."),
    ("azithromycin", "omeprazole", "Some antibiotics can interact with acid-reducing medicines - timing may need adjusting."),
    ("ibuprofen", "metformin", "NSAIDs can sometimes affect kidney function, which matters for diabetes medicines."),
]


def _normalize(name: str) -> str:
    return name.strip().lower()


def _lookup(name: str) -> MedicineInfo:
    return _MEDICINE_INFO.get(_normalize(name), _GENERIC_DEFAULT)


def get_medicine_info(name: str) -> dict:
    info = _lookup(name)
    cheaper_available = bool(info.generic_price_inr and info.generic_price_inr < info.branded_price_inr)
    return {
        "medicine_name": name,
        "description": info.description,
        "drug_class": info.drug_class,
        "common_uses": info.common_uses,
        "pricing": {
            "branded_price_inr": info.branded_price_inr or None,
            "generic_name": info.generic_name or None,
            "generic_price_inr": info.generic_price_inr or None,
            "cheaper_generic_available": cheaper_available,
            "source": info.price_source if (info.branded_price_inr or info.generic_price_inr) else None,
        },
    }


def get_interaction_flags(medicine_names: list[str]) -> list[dict]:
    """Informational only: flags pairs worth confirming with a doctor or
    pharmacist. Never a diagnosis, never a directive to stop/change/
    substitute a medication."""
    normalized = [_normalize(n) for n in medicine_names]
    flags = []
    for med_a, med_b, note in _INTERACTION_PAIRS:
        if med_a in normalized and med_b in normalized:
            # Report using the original casing the caller provided.
            name_a = next(n for n in medicine_names if _normalize(n) == med_a)
            name_b = next(n for n in medicine_names if _normalize(n) == med_b)
            flags.append(
                {
                    "medicines": [name_a, name_b],
                    "note": note,
                    "recommendation": "Please confirm this combination with your doctor or pharmacist.",
                }
            )
    return flags


def get_medicine_insights(medicine_names: list[str]) -> dict:
    return {
        "medicines": [get_medicine_info(name) for name in medicine_names],
        "interaction_flags": get_interaction_flags(medicine_names),
        "disclaimer": (
            "This information is for general reference only (demo data), not a medical "
            "diagnosis or prescribing decision. Always confirm with your doctor or "
            "pharmacist before making any changes to your medication."
        ),
    }
