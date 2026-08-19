from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Appointment, MedicalRecord, Patient
from .schemas import AppointmentRead, MedicalRecordRead, PatientCreate, PatientRead

router = APIRouter(tags=["patients"])


@router.get("/patients/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: int, db: Session = Depends(get_db)) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("/patients", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)) -> Patient:
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/patients/{patient_id}/appointments", response_model=list[AppointmentRead])
def get_appointments(patient_id: int, db: Session = Depends(get_db)) -> list[Appointment]:
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return list(db.scalars(select(Appointment).where(Appointment.patient_id == patient_id)))


@router.get("/patients/{patient_id}/records", response_model=list[MedicalRecordRead])
def get_records(patient_id: int, db: Session = Depends(get_db)) -> list[MedicalRecord]:
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return list(db.scalars(select(MedicalRecord).where(MedicalRecord.patient_id == patient_id)))
