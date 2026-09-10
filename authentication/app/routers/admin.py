from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import RoleRequired, get_current_user_with_scope_check
from app.models import User, UserResponse

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(RoleRequired("admin"))]
)


@router.get(
    "/users",
    response_model=list[UserResponse],
    dependencies=[Security(get_current_user_with_scope_check, scopes=["read:users"])],
)
def get_all_users(session: SessionDep):
    return session.exec(select(User)).all()


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Security(get_current_user_with_scope_check, scopes=["delete:users"])],
)
def delete_user(session: SessionDep, user_id: int):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    session.delete(user)
    session.commit()
