import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from app.database import SessionDep
from app.models import (
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetToken,
    User,
    UserCreate,
    UserResponse,
)
from app.security import (
    DUMMY_HASH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def register(session: SessionDep, user_data: UserCreate):
    existing_user = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    new_user = User(
        email=user_data.email, hashed_password=hash_password(user_data.password)
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user


@router.post("/token")
def login(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    existing_user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not existing_user:
        verify_password(form_data.password, DUMMY_HASH)
        raise credentials_exception

    if not verify_password(form_data.password, existing_user.hashed_password):
        raise credentials_exception

    data = {"sub": existing_user.email}
    access_token = create_access_token(data=data)
    refresh_token = create_refresh_token(data=data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/token/refresh")
def refresh_token(session: SessionDep, refresh_token: Annotated[str, Body(embed=True)]):
    invalid_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
    )

    payload = decode_token(refresh_token)
    if not payload:
        raise invalid_token_exception

    if payload.get("type") != "refresh":
        raise invalid_token_exception

    email = payload.get("sub")
    if not email:
        raise invalid_token_exception

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise invalid_token_exception

    new_access_token = create_access_token(data={"sub": user.email})
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/password-reset/request")
def request_password_reset(session: SessionDep, payload: PasswordResetRequest):
    message = {
        "message": "If an account exists with this email, a reset link has been sent"
    }

    user = session.exec(select(User).where(User.email == payload.email)).first()

    if not user or not user.id:
        return message

    token = secrets.token_urlsafe(32)

    reset_token = PasswordResetToken(
        token=token,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        used=False,
    )
    session.add(reset_token)
    session.commit()
    # In production: send an email to the user with the contents of token
    # Here's the link to you reset your password
    # i.e. send_reset_email(user.email, token)

    return message


@router.post("/password-reset/confirm")
def confirm_password_reset(session: SessionDep, payload: PasswordResetConfirm):
    invalid_token_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid reset token",
    )

    reset_token = session.exec(
        select(PasswordResetToken).where(PasswordResetToken.token == payload.token)
    ).first()

    if not reset_token:
        raise invalid_token_error

    if reset_token.used:
        raise invalid_token_error

    token_expired = reset_token.expires_at < datetime.now(UTC).replace(tzinfo=None)
    if token_expired:
        raise invalid_token_error

    user = session.get(User, reset_token.user_id)
    if not user:
        raise invalid_token_error

    user.hashed_password = hash_password(payload.new_password)
    session.add(user)

    reset_token.used = True
    session.add(reset_token)

    session.commit()

    return {"message": "Password reset successfully"}
