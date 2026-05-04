from typing import Optional

from fastapi import HTTPException
from fastapi import Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from starlette.status import HTTP_401_UNAUTHORIZED


class OAuth2PasswordBearerFromCookie(OAuth2PasswordBearer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __call__(self, request: Request) -> Optional[str]:
        # Get access token from httpOnly cookie instead of authorization header.
        # authorization: str = request.headers.get("Authorization")
        authorization: str = request.cookies.get("access_token")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param
