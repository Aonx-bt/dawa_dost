"""Informational medicine insights: what a medicine is for, a cheaper
generic equivalent, and interaction flags to confirm with a doctor/
pharmacist. Uses dummy reference data (see app/services/medicine_reference.py).

This endpoint never diagnoses, never recommends stopping/changing/
substituting a medication - it only surfaces information for the patient
to bring to their doctor or pharmacist.
"""
from fastapi import APIRouter

from app.schemas.schemas import MedicineInsightsRequest, MedicineInsightsResponse
from app.services.medicine_reference import get_medicine_insights

router = APIRouter(prefix="/api/medicine-insights", tags=["medicine-insights"])


@router.post("", response_model=MedicineInsightsResponse)
def medicine_insights(body: MedicineInsightsRequest):
    return get_medicine_insights(body.medicine_names)
