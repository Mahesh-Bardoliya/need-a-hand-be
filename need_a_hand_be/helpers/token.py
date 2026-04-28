from datetime import UTC
from datetime import datetime as dt
from datetime import timedelta as td

from fastapi import Request
from jose import JWTError
from jose import jwt

from ..config import settings
from ..models import User
from ..schemas.token import TokenData
from .errors_and_exceptions import raise_credentials_exception


def create_access_token(
    data: dict,
    secret_key: str,
    jwt_algorithm: str,
    expires_minutes: int,
    expires_delta: td = None,
):
    to_encode = data.copy()
    expire = dt.now(UTC).replace(tzinfo=None) + (
        expires_delta or td(minutes=expires_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=jwt_algorithm)


def decode_token(
    token: str,
    secret_key: str,
    jwt_algorithm: str,
):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[jwt_algorithm])
        username: str = payload.get("email")
        email: str = payload.get("email")
        if username is None:
            raise_credentials_exception()
        token_data = TokenData(username=username, email=email)
    except JWTError:
        raise_credentials_exception()
    return token_data


def decode_token_wrapper(
    token_string: str,
    secret_key: str,
    jwt_algorithm: str,
):
    try:
        token = token_string.split(" ")[-1]
        token_data = jwt.decode(token, secret_key, algorithms=[jwt_algorithm])
        return token_data
    except JWTError:
        raise
