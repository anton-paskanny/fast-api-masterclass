from typing import Annotated

from fastapi import Depends, Path

from app.dependencies.database import SessionDep
from app.errors import USER_NOT_FOUND
from app.models.user import User

UserId = Annotated[int, Path(ge=1, description="The id of the user to fetch")]


async def get_user_or_404(session: SessionDep, user_id: UserId):
    user = await session.get(User, user_id)
    if not user:
        raise USER_NOT_FOUND
    return user


UserDep = Annotated[User, Depends(get_user_or_404)]
