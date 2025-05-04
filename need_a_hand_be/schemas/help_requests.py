import typing

from pydantic import BaseModel

from .help_offers import HelpOfferResponseSchema
from .user import UserResponseSchema
from .utils import UUIDSchema


class HelpRequestBaseSchema(BaseModel):
    title: str
    description: str
    location: str


class HelpRequestCreateSchema(HelpRequestBaseSchema):
    class Config:
        extra = "forbid"


class HelpRequestResponseSchema(HelpRequestBaseSchema, UUIDSchema):
    is_active: bool
    user: UserResponseSchema
    help_offers: list[HelpOfferResponseSchema]


class HelpRequestFilterSchema(BaseModel):
    is_active: typing.Optional[typing.Any] = None
    title: typing.Optional[typing.Any] = None
    location: typing.Optional[typing.Any] = None
