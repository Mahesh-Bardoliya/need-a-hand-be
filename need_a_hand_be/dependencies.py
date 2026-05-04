from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from .config import Settings
from .config import settings
from .constants import API_PREFIX
from .database import SessionLocal
from .helpers.errors_and_exceptions import raise_credentials_exception
from .helpers.oauth2 import OAuth2PasswordBearerFromCookie
from .helpers.token import decode_token
from .models import User


@lru_cache()
def get_settings():
    return settings


oauth2_scheme = OAuth2PasswordBearerFromCookie(tokenUrl=f"{API_PREFIX}/auth/login")


# Dependency: Get DB Session
async def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from contextvars import ContextVar

current_user_id_var: ContextVar[int] = ContextVar("current_user_id", default=None)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> User:
    token_data = decode_token(
        token, secret_key=settings.secret_key, jwt_algorithm=settings.jwt_algorithm
    )
    user = db_session.query(User).filter_by(email=token_data.email).first()
    if user is None:
        raise_credentials_exception()
    current_user_id_var.set(user.id)
    return user


async def get_current_user_for_refresh(
    token: str = Depends(oauth2_scheme),
    db_session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> User:
    from .helpers.token import decode_expired_token

    token_data = decode_expired_token(
        token, secret_key=settings.secret_key, jwt_algorithm=settings.jwt_algorithm
    )
    user = db_session.query(User).filter_by(email=token_data.email).first()
    if user is None:
        raise_credentials_exception()
    current_user_id_var.set(user.id)
    return user
