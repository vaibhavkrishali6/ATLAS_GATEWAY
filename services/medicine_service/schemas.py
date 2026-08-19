from pydantic import BaseModel, ConfigDict, Field


class MedicineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    manufacturer: str = Field(min_length=1, max_length=160)
    dosage: str = Field(min_length=1, max_length=80)
    stock_quantity: int = Field(ge=0)


class MedicineRead(MedicineCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PrescriptionRead(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    medicine_id: int
    dosage: str
    instructions: str
    model_config = ConfigDict(from_attributes=True)
