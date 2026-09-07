from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field, StringConstraints, field_validator
from sqlmodel import col, select

from app.dependencies.database import SessionDep
from app.models.room import Room, RoomBase, RoomPublic, RoomUpdate

router = APIRouter()


class RoomQueryParams(BaseModel):
    max_price: int | None = Field(
        default=None, ge=10, le=10_000, examples=[100, 2000, 10_000]
    )

    search: Annotated[str | None, StringConstraints(to_lower=True)] = Field(
        default=None,
        min_length=3,
        max_length=10,
        title="Search term",
        description="Provide a keyword to look for within the room's title",
        examples=["sunny", "bedroom", "house"],
    )

    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @field_validator("search")
    @classmethod
    def fail_if_funny(cls, search: str) -> str:
        if "lol" in search:
            raise ValueError("No funny business allowed")
        return search


RoomId = Annotated[int, Path(ge=1, description="The id of the room to fetch")]

MAINTENANCE_MODE = False


def check_maintenance_mode():
    if MAINTENANCE_MODE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is under maintenance. Try again later",
        )


async def get_room_or_404(session: SessionDep, room_id: RoomId):
    room = await session.get(Room, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
        )
    return room


RoomDep = Annotated[Room, Depends(get_room_or_404)]


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=RoomPublic,
    dependencies=[Depends(check_maintenance_mode)],
)
async def create_room(session: SessionDep, room: RoomBase):
    validated_room = Room.model_validate(room)
    session.add(validated_room)
    await session.commit()
    await session.refresh(validated_room)
    return validated_room


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[RoomPublic],
    summary="List all available rooms",
    description="Returns all rooms. Supports filtering by price and search term.",
    response_description="A list of rooms matching the filter criteria",
)
async def get_rooms(session: SessionDep, params: Annotated[RoomQueryParams, Query()]):
    statement = select(Room)

    if params.max_price:
        statement = statement.where(Room.price_per_night <= params.max_price)

    if params.search:
        statement = statement.where(col(Room.name).ilike(f"%{params.search}%"))

    statement = (
        statement.limit(params.limit).offset(params.offset).order_by(col(Room.id))
    )

    rooms = await session.exec(statement)
    return rooms.all()


@router.get(
    "/{room_id}",
    status_code=status.HTTP_200_OK,
    response_model=RoomPublic,
)
async def get_room(room: RoomDep):
    return room


@router.patch(
    "/{room_id}",
    status_code=status.HTTP_200_OK,
    response_model=RoomPublic,
    dependencies=[Depends(check_maintenance_mode)],
)
async def update_room(session: SessionDep, room: RoomDep, room_payload: RoomUpdate):
    room_payload_without_default_values = room_payload.model_dump(exclude_unset=True)
    room.sqlmodel_update(room_payload_without_default_values)
    session.add(room)
    await session.commit()
    await session.refresh(room)
    return room


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_200_OK,
    response_model=RoomPublic,
    dependencies=[Depends(check_maintenance_mode)],
)
async def delete_room(session: SessionDep, room: RoomDep):
    await session.delete(room)
    await session.commit()
    return room
