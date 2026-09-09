from typing import Annotated

from fastapi import APIRouter, Path, status
from sqlalchemy.orm import joinedload

from app.dependencies.database import SessionDep
from app.errors import BOOKING_NOT_FOUND, ROOM_NOT_FOUND, USER_NOT_FOUND
from app.models.booking import Booking, BookingBase, BookingPublic
from app.models.room import Room
from app.models.user import User
from app.schemas.responses import BookingWithDetails

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BookingPublic)
async def create_booking(session: SessionDep, booking: BookingBase):
    room = await session.get(Room, booking.room_id)
    if not room:
        raise ROOM_NOT_FOUND

    user = await session.get(User, booking.user_id)
    if not user:
        raise USER_NOT_FOUND

    validated_booking = Booking.model_validate(booking)
    session.add(validated_booking)
    await session.commit()
    await session.refresh(validated_booking)
    return validated_booking


@router.get(
    "/{booking_id}", status_code=status.HTTP_200_OK, response_model=BookingWithDetails
)
async def get_booking(session: SessionDep, booking_id: Annotated[int, Path(ge=1)]):
    booking = await session.get(
        Booking,
        booking_id,
        options=[joinedload(Booking.room), joinedload(Booking.user)],  # type:ignore
    )
    if not booking:
        raise BOOKING_NOT_FOUND

    return booking
