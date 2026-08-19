from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Medicine, Prescription
from .schemas import MedicineCreate, MedicineRead, PrescriptionRead

router = APIRouter(tags=["medicines"])


@router.get("/medicines", response_model=list[MedicineRead])
def list_medicines(db: Session = Depends(get_db)) -> list[Medicine]:
    return list(db.scalars(select(Medicine)))


@router.get("/medicines/{medicine_id}", response_model=MedicineRead)
def get_medicine(medicine_id: int, db: Session = Depends(get_db)) -> Medicine:
    medicine = db.get(Medicine, medicine_id)
    if medicine is None:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return medicine


@router.post("/medicines", response_model=MedicineRead, status_code=status.HTTP_201_CREATED)
def create_medicine(payload: MedicineCreate, db: Session = Depends(get_db)) -> Medicine:
    medicine = Medicine(**payload.model_dump())
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.get("/prescriptions/{prescription_id}", response_model=PrescriptionRead)
def get_prescription(prescription_id: int, db: Session = Depends(get_db)) -> Prescription:
    prescription = db.get(Prescription, prescription_id)
    if prescription is None:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return prescription
