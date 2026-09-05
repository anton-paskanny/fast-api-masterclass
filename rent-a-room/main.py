from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StringConstraints, field_validator
from sqlmodel import col, select

from database import SessionDep, create_db_and_tables
from models import Room, RoomBase, RoomPublic, RoomUpdate

openapi_tags = [
    {
        "name": "rooms",
        "description": "Operations with **rooms** (a 4-wall _space_ that can be slept in)",
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Rent a Room API",
    description="Book a stay in a house or room",
    version="1.0.0",
    contact={"name": "Boris Enterprises LTD", "email": "boris@example.com"},
    openapi_tags=openapi_tags,
)

app.mount("/assets", StaticFiles(directory="assets"), name="assets")


class AppCookies(BaseModel):
    theme: Literal["light", "dark"] = "dark"
    language: Literal["en", "es", "fr"] = "en"


class AppHeaders(BaseModel):
    user_agent: str | None


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


def get_room_or_404(session: SessionDep, room_id: RoomId):
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
        )
    return room


RoomDep = Annotated[Room, Depends(get_room_or_404)]


@app.get("/", status_code=status.HTTP_200_OK)
def root(
    app_cookies: Annotated[AppCookies, Cookie()],
    app_headers: Annotated[AppHeaders, Header()],
):
    greetings = {
        "en": "Welcome to Rent a Room",
        "es": "Bienvenido a Rent a Room",
        "fr": "Bienvenue a Rent a Room",
    }
    greeting = greetings.get(app_cookies.language)

    return {
        "message": greeting,
        "user_agent": app_headers.user_agent,
    }


@app.post(
    "/rooms",
    status_code=status.HTTP_201_CREATED,
    tags=["rooms"],
    response_model=RoomPublic,
)
def create_room(session: SessionDep, room: RoomBase):
    validated_room = Room.model_validate(room)
    session.add(validated_room)
    session.commit()
    session.refresh(validated_room)
    return validated_room


@app.get(
    "/rooms",
    status_code=status.HTTP_200_OK,
    response_model=list[RoomPublic],
    tags=["rooms"],
    summary="List all available rooms",
    description="Returns all rooms. Supports filtering by price and search term.",
    response_description="A list of rooms matching the filter criteria",
)
def get_rooms(session: SessionDep, params: Annotated[RoomQueryParams, Query()]):
    statement = select(Room)

    if params.max_price:
        statement = statement.where(Room.price_per_night <= params.max_price)

    if params.search:
        statement = statement.where(col(Room.name).ilike(f"%{params.search}%"))

    statement = (
        statement.limit(params.limit).offset(params.offset).order_by(col(Room.id))
    )

    return session.exec(statement).all()


@app.get(
    "/rooms/{room_id}",
    status_code=status.HTTP_200_OK,
    response_model=RoomPublic,
    tags=["rooms"],
)
def get_room(room: RoomDep):
    return room


@app.patch(
    "/rooms/{room_id}",
    status_code=status.HTTP_200_OK,
    response_model=RoomPublic,
    tags=["rooms"],
)
def update_room(session: SessionDep, room: RoomDep, room_payload: RoomUpdate):
    room_payload_without_default_values = room_payload.model_dump(exclude_unset=True)
    room.sqlmodel_update(room_payload_without_default_values)
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


@app.delete(
    "/rooms/{room_id}",
    status_code=status.HTTP_200_OK,
    response_model=RoomPublic,
    tags=["rooms"],
)
def delete_room(session: SessionDep, room: RoomDep):
    session.delete(room)
    session.commit()
    return room


@app.get("/preferences", status_code=status.HTTP_200_OK, tags=["preferences"])
def set_preferences(response: Response):
    app_cookies = AppCookies()

    response.set_cookie(key="theme", value=app_cookies.theme)
    response.set_cookie(key="language", value=app_cookies.language)
    return {"message": "Preferences updated"}
