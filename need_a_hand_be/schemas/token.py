import typing

from pydantic import BaseModel
from pydantic import EmailStr


class TokenData(BaseModel):
    email: typing.Optional[EmailStr] = None
    username: typing.Optional[str] = None
