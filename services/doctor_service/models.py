from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Doctor(Base):
    __tablename__ = "doctors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    specialization: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone: Mapped[str] = mapped_column(String(32))
    availability: Mapped[bool] = mapped_column(Boolean, default=True)


class DoctorAppointment(Base):
    __tablename__ = "doctor_appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    patient_id: Mapped[int] = mapped_column(Integer)  # Reference only: patient_db is never queried.
    appointment_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32))
