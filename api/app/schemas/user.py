from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole
    active: bool = True
    team: str | None = None


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: UserRole
    password: str
    team: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None
    active: bool | None = None
    team: str | None = None
    password: str | None = None


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True
