from pydantic import Field

from .user import UserBaseSchema


class UserRegister(UserBaseSchema):
    password: str = Field(min_length=8, max_length=128)
