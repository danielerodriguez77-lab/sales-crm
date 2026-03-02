from datetime import datetime

from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    sku: str
    price: float


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    price: float | None = None


class ProductRead(ProductBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
