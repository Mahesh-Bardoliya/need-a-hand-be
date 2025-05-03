from .user import UserBaseSchema


class UserRegister(UserBaseSchema):
    password: str
