from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Medicine(Base):
    __tablename__ = "medicines"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    manufacturer: Mapped[str] = mapped_column(String(160))
    dosage: Mapped[str] = mapped_column(String(80))
    stock_quantity: Mapped[int] = mapped_column(Integer)


class Prescription(Base):
    __tablename__ = "prescriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(Integer)  # External reference only.
    doctor_id: Mapped[int] = mapped_column(Integer)  # External reference only.
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id"))
    dosage: Mapped[str] = mapped_column(String(80))
    instructions: Mapped[str] = mapped_column(Text)
