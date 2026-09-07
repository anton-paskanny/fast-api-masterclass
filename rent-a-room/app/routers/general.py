from typing import Annotated, Literal

from fastapi import APIRouter, Cookie, Header, Response, status
from pydantic import BaseModel

router = APIRouter()


class AppCookies(BaseModel):
    theme: Literal["light", "dark"] = "dark"
    language: Literal["en", "es", "fr"] = "en"


class AppHeaders(BaseModel):
    user_agent: str | None


@router.get("/", status_code=status.HTTP_200_OK)
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


@router.get("/preferences", status_code=status.HTTP_200_OK, tags=["preferences"])
def set_preferences(response: Response):
    app_cookies = AppCookies()

    response.set_cookie(key="theme", value=app_cookies.theme)
    response.set_cookie(key="language", value=app_cookies.language)
    return {"message": "Preferences updated"}
