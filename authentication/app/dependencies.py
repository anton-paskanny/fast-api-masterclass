from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlmodel import select

from app.database import SessionDep
from app.models import User
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scopes={
    "read:users": "Read users",
    "write:users": "Create and update users",
    "delete:users": "Delete users"
})


def get_current_user(
    session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    invalid_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if not payload:
        raise invalid_token_exception

    if payload.get("type") != "access":
        raise invalid_token_exception

    email = payload.get("sub")
    if not email:
        raise invalid_token_exception

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise invalid_token_exception

    return user


def get_current_user_with_scope_check(
    current_user: Annotated[User, Depends(get_current_user)],
    token: Annotated[str, Depends(oauth2_scheme)],
    security_scopes: SecurityScopes,
) -> User:
    payload = decode_token(token)
    assert payload is not None

    user_scopes = payload.get("scopes", [])

    for scope in security_scopes.scopes:
        if scope not in user_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]

Role = Literal["user", "admin"]

class RoleRequired:
    def __init__(self, role: Role):
        self.role = role

    def __call__(self, current_user: CurrentUser):
        if current_user.role != self.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires the '{self.role}' role"
            )
        return current_user
