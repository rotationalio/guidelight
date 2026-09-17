"""Shared types for high-level response models and request payloads."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import ciso8601


def parse_datetime(value: Any) -> datetime | None:
    """Parse an Endeavor timestamp while accepting an absent value."""
    if value is None or isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise TypeError(f"expected an ISO-8601 timestamp, got {type(value).__name__}")
    return ciso8601.parse_datetime(value)


def serialize_value(value: Any) -> Any:
    """Convert request objects and datetime values into JSON-compatible values."""
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, tuple):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_value(item) for key, item in value.items()}
    return value


class ResponseModel:
    """Base class for server responses.

    Response models describe what the server returned. They intentionally do not
    provide an implicit writable serialization path.
    """

    _extra: dict[str, Any]

    @classmethod
    def _known_fields(cls) -> set[str]:
        return set()

    @classmethod
    def _extras(cls, data: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in data.items()
            if key not in cls._known_fields()
        }
