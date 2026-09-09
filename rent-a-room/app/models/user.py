from typing import TYPE_CHECKING

from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.booking import Booking


class UserBase(SQLModel):
    name: str
    email: EmailStr
    phone: PhoneNumber


class User(UserBase, table=True):
    __tablename__: str = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True)

    bookings: list["Booking"] = Relationship(back_populates="user")


class UserPublic(UserBase):
    id: int
