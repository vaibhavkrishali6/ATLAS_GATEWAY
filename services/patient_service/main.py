from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI
from sqlalchemy import select

from .database import get_engine, get_session_factory
from .models import Appointment, Base, MedicalRecord, Patient
from .routes import router


def initialize_database() -> None:
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        if db.scalar(select(Patient.id).limit(1)) is None:
            patient = Patient(name="Mira Stone", age=34, gender="female", phone="555-0101", email="mira.stone@example.test")
            db.add(patient)
            db.flush()
            db.add_all([Appointment(patient_id=patient.id, doctor_name="Dr. Rowan Vale", appointment_date=date(2026, 9, 1), status="scheduled"), MedicalRecord(patient_id=patient.id, diagnosis="Seasonal allergy", notes="Fictional sample record.")])
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Patient Service", lifespan=lifespan)
app.include_router(router)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "patient-service"}
