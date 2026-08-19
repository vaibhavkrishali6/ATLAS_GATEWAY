from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=0, le=130)
    gender: str = Field(min_length=1, max_length=32)
    phone: str = Field(min_length=1, max_length=32)
    email: str = Field(min_length=3, max_length=255)


class PatientRead(PatientCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class AppointmentRead(BaseModel):
    id: int
    patient_id: int
    doctor_name: str
    appointment_date: date
    status: str
    model_config = ConfigDict(from_attributes=True)


class MedicalRecordRead(BaseModel):
    id: int
    patient_id: int
    diagnosis: str
    notes: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
