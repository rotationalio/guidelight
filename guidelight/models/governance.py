"""Model governance policy response and request models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import JsonValue, field_validator

from .base import RequestModel, ResponseModel, TrimmedNonEmptyString

PolicyType = Literal["license", "model"]


class GovernancePolicy(ResponseModel):
    """A model governance policy."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    name: str = ""
    description: str = ""
    policy_type: Any = None
    provider_id: str | None = None
    constraints: Any = None
    active: bool | None = None


class GovernancePolicyCreate(RequestModel):
    """Writable governance policy fields."""

    name: TrimmedNonEmptyString
    description: str = ""
    policy_type: PolicyType
    provider_id: str | None = None
    constraints: JsonValue
    active: bool = True

    @field_validator("constraints")
    @classmethod
    def require_constraints(cls, value: JsonValue) -> JsonValue:
        """Reject values that Endeavor treats as missing constraints."""
        if value is None or value == {} or value == []:
            raise ValueError("constraints must not be empty")
        return value


class GovernancePolicyPatch(RequestModel):
    """Partial governance policy update fields."""

    name: TrimmedNonEmptyString | None = None
    description: str | None = None
    policy_type: PolicyType | None = None
    provider_id: str | None = None
    constraints: JsonValue | None = None
    active: bool | None = None
