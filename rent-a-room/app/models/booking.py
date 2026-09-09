from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.user import User


class BookingBase(SQLModel):
    room_id: int
    user_id: int
    check_in: datetime
    check_out: datetime


class Booking(BookingBase, table=True):
    __tablename__: str = "bookings"

    id: int | None = Field(default=None, primary_key=True)
    room_id: int | None = Field(foreign_key="rooms.id", ondelete="SET NULL")
    user_id: int = Field(foreign_key="users.id")

    room: Optional["Room"] = Relationship(back_populates="bookings")
    user: "User" = Relationship(back_populates="bookings")


class BookingPublic(BookingBase):
    id: int
    room_id: int | None
