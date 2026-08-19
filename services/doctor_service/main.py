from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI
from sqlalchemy import select

from .database import get_engine, get_session_factory
from .models import Base, Doctor, DoctorAppointment
from .routes import router


def initialize_database() -> None:
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        if db.scalar(select(Doctor.id).limit(1)) is None:
            doctor = Doctor(name="Dr. Rowan Vale", specialization="General Medicine", email="rowan.vale@example.test", phone="555-0201", availability=True)
            db.add(doctor)
            db.flush()
            db.add(DoctorAppointment(doctor_id=doctor.id, patient_id=1, appointment_date=date(2026, 9, 1), status="scheduled"))
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Doctor Service", lifespan=lifespan)
app.include_router(router)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "doctor-service"}
