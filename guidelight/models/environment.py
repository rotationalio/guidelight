"""Environment response and request models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import model_validator

from .base import RequestModel, ResponseModel, TrimmedNonEmptyString


class EnvironmentProviderReference(RequestModel):
    """Provider identifier accepted by Environment write requests."""

    id: TrimmedNonEmptyString


class Environment(ResponseModel):
    """A deployment environment returned by Endeavor."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    provider: dict[str, Any] | None = None
    name: str = ""
    slug: str = ""
    description: str = ""
    version: str = ""
    region: int | None = None
    is_default: bool = False


class EnvironmentCreate(RequestModel):
    """Writable fields accepted when creating an environment."""

    name: TrimmedNonEmptyString
    slug: TrimmedNonEmptyString
    description: str = ""
    version: str = ""
    region: int | None = None
    provider: EnvironmentProviderReference | None = None
    is_default: bool = False


class EnvironmentUpdate(RequestModel):
    """Complete writable environment representation used by PUT."""

    name: TrimmedNonEmptyString
    slug: TrimmedNonEmptyString
    description: str = ""
    version: str = ""
    region: int | None = None
    provider: EnvironmentProviderReference | None = None
    is_default: bool = False


class EnvironmentPatch(RequestModel):
    """Partial environment update used by PATCH."""

    name: TrimmedNonEmptyString | None = None
    slug: TrimmedNonEmptyString | None = None
    description: str | None = None
    version: str | None = None
    region: int | None = None
    provider: EnvironmentProviderReference | None = None
    is_default: bool | None = None

    @model_validator(mode="after")
    def validate_patch(self) -> EnvironmentPatch:
        """Reject an empty PATCH or an attempt to unset the default."""
        if not self.model_dump(exclude_none=True):
            raise ValueError("at least one Environment field is required")
        if self.is_default is False:
            raise ValueError("is_default must be true when specified")
        return self
