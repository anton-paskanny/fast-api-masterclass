from sqlmodel import Field, SQLModel


# Base model class - shared fields for all representations of a room
class RoomBase(SQLModel):
    name: str = Field()
    price_per_night: int = Field()
    bedrooms: float = Field(multiple_of=0.5)
    bathrooms: float = Field(multiple_of=0.5)


# Room table model - maps to the "rooms" database table
class Room(RoomBase, table=True):
    __tablename__: str = "rooms"

    id: int | None = Field(default=None, primary_key=True)


# Room response model - the payload to send back to the client
# Guaranteed to have ID for the room (room must exist)
class RoomPublic(RoomBase):
    id: int


# Room update model - all fields can be optional becaue
# we fallback to None
class RoomUpdate(SQLModel):
    name: str | None = None
    price_per_night: int | None = None
    bedrooms: float | None = None
    bathrooms: float | None = None
