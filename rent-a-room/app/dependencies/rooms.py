from typing import Annotated

from fastapi import Depends, Path

from app.dependencies.database import SessionDep
from app.errors import ROOM_NOT_FOUND
from app.models.room import Room

RoomId = Annotated[int, Path(ge=1, description="The id of the room to fetch")]


async def get_room_or_404(session: SessionDep, room_id: RoomId):
    room = await session.get(Room, room_id)
    if not room:
        raise ROOM_NOT_FOUND
    return room


RoomDep = Annotated[Room, Depends(get_room_or_404)]
