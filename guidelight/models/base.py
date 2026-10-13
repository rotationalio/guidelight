"""Shared types for high-level response models and request payloads."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel, ConfigDict


class ResponseModel(BaseModel):
    """A server response with preserved, inspectable unknown fields."""

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResponseModel:
        """Build a response model from an API response dictionary."""
        return cls.model_validate(data)

    @property
    def extra(self) -> Mapping[str, Any]:
        """Return unknown response fields as a read-only mapping."""
        return MappingProxyType(self.model_extra or {})


class RequestModel(BaseModel):
    """A strict, explicitly writable request body."""

    model_config = ConfigDict(extra="forbid")

    def to_dict(self) -> dict[str, Any]:
        """Serialize writable fields for an API request body."""
        return self.model_dump(mode="json", exclude_none=True)
