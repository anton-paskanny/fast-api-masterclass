from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class UserCreate(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)


class User(SQLModel, table=True):
    __tablename__: str = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True)
    hashed_password: str
    role: str = Field(default="user")


class UserUpdate(SQLModel):
    email: EmailStr | None = None


class UserResponse(SQLModel):
    id: int
    email: str
    role: str


class PasswordResetRequest(SQLModel):
    email: EmailStr


class PasswordResetToken(SQLModel, table=True):
    __tablename__: str = "password_reset_tokens"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    used: bool = Field(default=False)


class PasswordResetConfirm(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=16)
