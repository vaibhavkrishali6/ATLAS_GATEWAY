from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class DoctorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    specialization: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    phone: str = Field(min_length=1, max_length=32)
    availability: bool = True


class DoctorRead(DoctorCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class DoctorAppointmentRead(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    appointment_date: date
    status: str
    model_config = ConfigDict(from_attributes=True)


class PatientReference(BaseModel):
    patient_id: int
