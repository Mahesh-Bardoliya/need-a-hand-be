#!/usr/bin/env python
# -*- coding: utf-8 -*-


from typing import Generic
from typing import List
from typing import TypeVar
from uuid import UUID

from humps import camelize
from humps import kebabize
from pydantic import BaseModel
from pydantic import ConfigDict

# Can be anything (type)
T = TypeVar("T")


class CamelCaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=camelize, populate_by_name=True)


class KebabCaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=kebabize, populate_by_name=True)


class DisallowExtraFieldModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# Generic schema for paginated response.
class PaginatedResponse(CamelCaseModel, BaseModel, Generic[T]):
    items: List[T]
    size: int
    page: int


class UUIDSchema(BaseModel):
    uuid: UUID
