from datetime import datetime as dt
from uuid import UUID

from pydantic import BaseModel

from .user import UserResponseSchema


class HelpOfferBaseSchema(BaseModel):
    message: str


class HelpOfferCreateSchema(HelpOfferBaseSchema):
    help_request_uuid: UUID

    class Config:
        extra = "forbid"


class HelpOfferResponseSchema(HelpOfferBaseSchema):
    is_accepted: bool
    help_request_uuid: UUID
    help_request_title: str
    helper: UserResponseSchema
    created_at: dt
