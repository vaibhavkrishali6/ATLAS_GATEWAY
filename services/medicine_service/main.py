from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from .database import get_engine, get_session_factory
from .models import Base, Medicine, Prescription
from .routes import router


def initialize_database() -> None:
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        if db.scalar(select(Medicine.id).limit(1)) is None:
            medicine = Medicine(name="Novalune", manufacturer="Fictional Labs", dosage="10 mg", stock_quantity=75)
            db.add(medicine)
            db.flush()
            db.add(Prescription(patient_id=1, doctor_id=1, medicine_id=medicine.id, dosage="10 mg", instructions="Take once daily with water."))
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Medicine Service", lifespan=lifespan)
app.include_router(router)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "medicine-service"}
