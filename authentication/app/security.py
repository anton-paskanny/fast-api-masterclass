from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.settings import settings

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummy-password-for-timing-attack-prevention")
ACCESS_TOKEN_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION_TIME_IN_MINUTES = 10
REFRESH_TOKEN_EXPIRATION_TIME_IN_DAYS = 7


# -------- PASSWORD GENERATION AND VERIFICATION
def hash_password(plain_password: str) -> str:
    return password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


# --------- JWT GENERATION + ENCODING/DECODING
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(UTC)

    if expires_delta:
        expiration_time = now + expires_delta
    else:
        expiration_time = now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRATION_TIME_IN_MINUTES
        )

    payload = {**data, "iat": now, "exp": expiration_time, "type": "access"}
    return jwt.encode(
        payload=payload, key=settings.JWT_SECRET_KEY, algorithm=ACCESS_TOKEN_ALGORITHM
    )


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(UTC)

    if expires_delta:
        expiration_time = now + expires_delta
    else:
        expiration_time = now + timedelta(days=REFRESH_TOKEN_EXPIRATION_TIME_IN_DAYS)

    payload = {**data, "iat": now, "exp": expiration_time, "type": "refresh"}

    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=ACCESS_TOKEN_ALGORITHM
    )


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, key=settings.JWT_SECRET_KEY, algorithms=[ACCESS_TOKEN_ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None
