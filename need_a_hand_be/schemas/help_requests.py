import typing
from datetime import datetime as dt

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from .help_offers import HelpOfferResponseSchema
from .user import UserResponseSchema
from .utils import UUIDSchema


class HelpRequestBaseSchema(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=2000)
    location: str = Field(min_length=2, max_length=150)


class HelpRequestCreateSchema(HelpRequestBaseSchema):
    model_config = ConfigDict(extra="forbid")


class HelpRequestResponseSchema(HelpRequestBaseSchema, UUIDSchema):
    is_active: bool
    user: UserResponseSchema
    help_offers: list[HelpOfferResponseSchema]
    created_at: dt


class HelpRequestFilterSchema(BaseModel):
    is_active: typing.Optional[bool] = None
    title: typing.Optional[str] = None
    location: typing.Optional[str] = None


class HelpRequestPaginatePayload(BaseModel):
    query: HelpRequestFilterSchema = Field(default_factory=HelpRequestFilterSchema)
    search: typing.Optional[str] = None
    sorting: dict[str, typing.Literal["asc", "desc"]] = Field(default_factory=dict)
