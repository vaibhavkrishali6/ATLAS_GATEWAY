from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Doctor, DoctorAppointment
from .schemas import DoctorAppointmentRead, DoctorCreate, DoctorRead, PatientReference

router = APIRouter(tags=["doctors"])


def require_doctor(doctor_id: int, db: Session) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.get("/doctors/{doctor_id}", response_model=DoctorRead)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)) -> Doctor:
    return require_doctor(doctor_id, db)


@router.post("/doctors", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)) -> Doctor:
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.get("/doctors/{doctor_id}/appointments", response_model=list[DoctorAppointmentRead])
def get_appointments(doctor_id: int, db: Session = Depends(get_db)) -> list[DoctorAppointment]:
    require_doctor(doctor_id, db)
    return list(db.scalars(select(DoctorAppointment).where(DoctorAppointment.doctor_id == doctor_id)))


@router.get("/doctors/{doctor_id}/patients", response_model=list[PatientReference])
def get_patients(doctor_id: int, db: Session = Depends(get_db)) -> list[PatientReference]:
    require_doctor(doctor_id, db)
    patient_ids = db.scalars(select(DoctorAppointment.patient_id).where(DoctorAppointment.doctor_id == doctor_id).distinct())
    return [PatientReference(patient_id=patient_id) for patient_id in patient_ids]
