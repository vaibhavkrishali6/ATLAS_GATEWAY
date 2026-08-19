from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(32))
    phone: Mapped[str] = mapped_column(String(32))
    email: Mapped[str] = mapped_column(String(255), unique=True)


class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_name: Mapped[str] = mapped_column(String(120))
    appointment_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32))


class MedicalRecord(Base):
    __tablename__ = "medical_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    diagnosis: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
