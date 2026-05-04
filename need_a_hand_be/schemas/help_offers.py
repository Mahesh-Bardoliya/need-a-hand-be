from datetime import datetime as dt
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from .user import UserResponseSchema
from .utils import UUIDSchema


class HelpOfferBaseSchema(BaseModel):
    message: str = Field(min_length=5, max_length=1000)


class HelpOfferCreateSchema(HelpOfferBaseSchema):
    help_request_uuid: UUID
    model_config = ConfigDict(extra="forbid")


class HelpOfferResponseSchema(HelpOfferBaseSchema, UUIDSchema):
    is_accepted: bool
    help_request_uuid: UUID
    help_request_title: str
    helper: UserResponseSchema
    created_at: dt
