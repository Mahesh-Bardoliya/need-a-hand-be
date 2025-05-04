from uuid import UUID

from pydantic import BaseModel
from pydantic import EmailStr

from .utils import UUIDSchema


class UserBaseSchema(BaseModel):
    name: str
    username: str
    email: EmailStr


class UserResponseSchema(UserBaseSchema, UUIDSchema):
    total_help_requests_count: int
    total_help_offers_count: int


class UserHelpOfferSchema(BaseModel):
    message: str
    is_accepted: bool
    help_request_uuid: UUID
    help_request_title: str
    helper: UserResponseSchema


class UserHelpRequestSchema(BaseModel):
    title: str
    description: str
    location: str
    is_active: bool
    help_offers: list[UserHelpOfferSchema]


class UserProfileResponseSchema(UserBaseSchema, UUIDSchema):
    total_help_requests_count: int
    total_help_offers_count: int
    help_requests: list[UserHelpRequestSchema]
    help_offers: list[UserHelpOfferSchema]
