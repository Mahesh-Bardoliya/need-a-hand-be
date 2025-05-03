from pydantic import BaseModel
from pydantic import EmailStr


class UserBaseSchema(BaseModel):
    name: str
    username: str
    email: EmailStr


class UserProfileSchema(UserBaseSchema):
    pass
