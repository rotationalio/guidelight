"""Provider and provider-credential models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from .base import RequestModel, ResponseModel, TrimmedNonEmptyString


class Provider(ResponseModel):
    """A provider and its server-managed status and catalog metadata."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    name: str = ""
    slug: str = ""
    link: str = ""
    description: str = ""
    provider_type: Any = None
    endpoint: str = ""
    api_type: Any = None
    catalog_url: str = ""
    catalog_cached: datetime | None = None
    auth_type: Any = None
    provider_extra: Any = Field(
        default=None,
        validation_alias="extra",
        serialization_alias="extra",
    )
    usage: Any = None
    status: Any = None
    is_default: bool = False


class ProviderCredential(ResponseModel):
    """Provider credential metadata without secret values."""

    provider_id: str | None = None
    secret_id: str | None = None
    name: str = ""
    auth_type: Any = None
    is_default: bool = False
    self_hosted: bool = False
    last_used: datetime | None = None
    created: datetime | None = None
    modified: datetime | None = None
    status: Any = None


class ProviderCredentialCreate(RequestModel):
    """Writable provider credential creation payload."""

    name: TrimmedNonEmptyString = "Provider Credential"
    credentials: dict[str, Any] = Field(min_length=1)
    is_default: bool = False
    self_hosted: bool = False


class ProviderCredentialUpdate(RequestModel):
    """Complete writable provider credential fields used by PUT."""

    name: TrimmedNonEmptyString | None = None
    is_default: bool = False

    @model_validator(mode="after")
    def require_update(self) -> ProviderCredentialUpdate:
        """Require a name change or promotion to the default credential."""
        if self.name is None and not self.is_default:
            raise ValueError("name or is_default=true is required")
        return self


class ProviderCredentialPatch(RequestModel):
    """Partial writable provider credential fields used by PATCH."""

    name: TrimmedNonEmptyString | None = None
    is_default: bool | None = None

    @model_validator(mode="after")
    def validate_patch(self) -> ProviderCredentialPatch:
        """Reject empty patches and attempts to unset the default credential."""
        if self.name is None and self.is_default is None:
            raise ValueError("at least one Provider Credential field is required")
        if self.is_default is False:
            raise ValueError("is_default must be true when specified")
        return self


class ProviderCreate(RequestModel):
    """Writable provider fields and the required initial credential."""

    name: TrimmedNonEmptyString
    endpoint: TrimmedNonEmptyString
    catalog_url: TrimmedNonEmptyString
    credential: ProviderCredentialCreate
    slug: TrimmedNonEmptyString | None = None
    provider_type: Any = None
    api_type: Any = None
    auth_type: Any = None
    link: str = ""
    description: str = ""
    extra: Any = None
    is_default: bool = False


class ProviderUpdate(RequestModel):
    """Complete writable provider fields used by PUT."""

    name: TrimmedNonEmptyString
    endpoint: TrimmedNonEmptyString
    catalog_url: TrimmedNonEmptyString
    slug: str = ""
    provider_type: Any = None
    api_type: Any = None
    link: str = ""
    description: str = ""
    extra: Any = None
    is_default: bool = False


class ProviderPatch(RequestModel):
    """Partial writable provider fields used by PATCH."""

    name: TrimmedNonEmptyString | None = None
    slug: TrimmedNonEmptyString | None = None
    link: str | None = None
    description: str | None = None
    provider_type: Any = None
    endpoint: TrimmedNonEmptyString | None = None
    api_type: Any = None
    catalog_url: TrimmedNonEmptyString | None = None
    extra: Any = None
    is_default: bool | None = None

    @model_validator(mode="after")
    def validate_patch(self) -> ProviderPatch:
        """Reject empty patches and attempts to unset the default provider."""
        if not self.model_dump(exclude_none=True):
            raise ValueError("at least one Provider field is required")
        if self.is_default is False:
            raise ValueError("is_default must be true when specified")
        return self


class ProviderStatusResponse(ResponseModel):
    """Result returned by a provider connectivity operation."""

    success: bool = False
    status: Any = None
    error: str = ""
