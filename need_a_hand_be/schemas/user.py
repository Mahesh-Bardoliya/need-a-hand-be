import typing
from datetime import datetime as dt
from uuid import UUID

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field

from .utils import UUIDSchema


class UserBaseSchema(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=3, max_length=32)
    email: EmailStr


class UserResponseSchema(UserBaseSchema, UUIDSchema):
    total_help_requests_count: int
    total_help_offers_count: int


class UserHelpOfferSchema(UUIDSchema):
    message: str
    is_accepted: bool
    help_request_uuid: UUID
    help_request_title: str
    helper: UserResponseSchema
    created_at: dt


class UserHelpRequestSchema(UUIDSchema):
    title: str
    description: str
    location: str
    is_active: bool
    help_offers: list[UserHelpOfferSchema]
    created_at: dt


class UserProfileResponseSchema(UserBaseSchema, UUIDSchema):
    total_help_requests_count: int
    total_help_offers_count: int
    help_requests: list[UserHelpRequestSchema]
    help_offers: list[UserHelpOfferSchema]
