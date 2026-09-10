from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser, get_current_user
from app.models import User, UserResponse, UserUpdate

router = APIRouter(dependencies=[Depends(get_current_user)], tags=["users"])


@router.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
def get_me(current_user: CurrentUser):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    session: SessionDep, current_user: CurrentUser, update_payload: UserUpdate
):
    if not update_payload.email:
        return current_user

    user_with_email = session.exec(
        select(User).where(User.email == update_payload.email)
    ).first()

    if user_with_email and user_with_email.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken"
        )

    current_user.email = update_payload.email

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user


@router.get("/dashboard")
def dashboard():
    return {"Profit": 1_000_000}
