"""Shared pydantic base classes + envelope types."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    """Base for response models that read from ORM instances."""

    model_config = ConfigDict(from_attributes=True)


class TimestampedDTO(ORMBase):
    created_at: datetime
    updated_at: datetime


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
