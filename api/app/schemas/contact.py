from datetime import datetime

from pydantic import BaseModel


class ContactBase(BaseModel):
    name: str
    tax_id: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    payment_terms: str | None = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    name: str | None = None
    tax_id: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    payment_terms: str | None = None


class ContactRead(ContactBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
