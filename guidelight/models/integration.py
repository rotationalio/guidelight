from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from urllib.parse import urlsplit

from pydantic import (
    AfterValidator,
    AliasChoices,
    Field,
    SecretStr,
    field_serializer,
    model_validator,
)

from .base import RequestModel, ResponseModel, TrimmedNonEmptyString

Role = str


def _validate_integration_endpoint(value: str) -> str:
    """Validate the absolute HTTP(S) endpoint required by Endeavor."""
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("endpoint must be a valid HTTP or HTTPS URL") from exc

    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or any(character.isspace() for character in parsed.netloc)
    ):
        raise ValueError("endpoint must be a valid HTTP or HTTPS URL")
    return value


_IntegrationEndpoint = Annotated[
    TrimmedNonEmptyString,
    AfterValidator(_validate_integration_endpoint),
]


class MCPPromptArgument(ResponseModel):
    """An argument accepted by a discovered MCP prompt."""

    description: str = ""
    name: str = ""
    required: bool = False
    title: str = ""


class MCPPrompt(ResponseModel):
    """A prompt discovered from an MCP Integration."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    integration_id: str | None = None
    meta: dict[str, Any] | None = Field(
        default=None, validation_alias=AliasChoices("_meta", "meta")
    )
    name: str = ""
    title: str = ""
    description: str = ""
    arguments: list[MCPPromptArgument] = Field(default_factory=list)
    is_deprecated: bool = Field(
        default=False, validation_alias=AliasChoices("isDeprecated", "is_deprecated")
    )


class MCPResourceAnnotations(ResponseModel):
    """Annotations advertised for an MCP resource."""

    audience: list[Role] = Field(default_factory=list)
    last_modified: str = Field(
        default="", validation_alias=AliasChoices("lastModified", "last_modified")
    )
    priority: float = 0.0


class MCPResource(ResponseModel):
    """A resource discovered from an MCP Integration."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    integration_id: str | None = None
    meta: dict[str, Any] | None = Field(
        default=None, validation_alias=AliasChoices("_meta", "meta")
    )
    description: str = ""
    mime_type: str = Field(
        default="", validation_alias=AliasChoices("mimeType", "mime_type")
    )
    name: str = ""
    size: int = 0
    title: str = ""
    uri: str = ""
    annotations: MCPResourceAnnotations | None = None
    is_deprecated: bool = Field(
        default=False, validation_alias=AliasChoices("isDeprecated", "is_deprecated")
    )


class MCPToolAnnotations(ResponseModel):
    """Annotations describing the behavior of an MCP tool."""

    destructive_hint: bool = Field(
        default=False,
        validation_alias=AliasChoices("destructiveHint", "destructive_hint"),
    )
    idempotent_hint: bool = Field(
        default=False,
        validation_alias=AliasChoices("idempotentHint", "idempotent_hint"),
    )
    open_world_hint: bool = Field(
        default=False, validation_alias=AliasChoices("openWorldHint", "open_world_hint")
    )
    read_only_hint: bool = Field(
        default=False, validation_alias=AliasChoices("readOnlyHint", "read_only_hint")
    )
    title: str = ""


class MCPTool(ResponseModel):
    """A tool discovered from an MCP Integration."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    integration_id: str | None = None
    meta: dict[str, Any] | None = Field(
        default=None, validation_alias=AliasChoices("_meta", "meta")
    )
    description: str = ""
    name: str = ""
    title: str = ""
    input_schema: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("inputSchema", "input_schema"),
    )
    output_schema: dict[str, Any] | None = Field(
        default=None, validation_alias=AliasChoices("outputSchema", "output_schema")
    )
    annotations: MCPToolAnnotations | None = None
    is_deprecated: bool = Field(
        default=False, validation_alias=AliasChoices("isDeprecated", "is_deprecated")
    )


class PromptCapability(ResponseModel):
    """Capabilities advertised for MCP prompts."""

    list_changed: bool = Field(
        default=False, validation_alias=AliasChoices("listChanged", "list_changed")
    )


class ResourceCapability(ResponseModel):
    """Capabilities advertised for MCP resources."""

    list_changed: bool = Field(
        default=False, validation_alias=AliasChoices("listChanged", "list_changed")
    )
    subscribe: bool = False


class ToolCapability(ResponseModel):
    """Capabilities advertised for MCP tools."""

    list_changed: bool = Field(
        default=False, validation_alias=AliasChoices("listChanged", "list_changed")
    )


class IntegrationCapabilities(ResponseModel):
    """Features advertised by an MCP server."""

    completions: dict[str, Any] | None = None
    experimental: dict[str, Any] | None = None
    logging: dict[str, Any] | None = None
    prompts: PromptCapability | None = None
    resources: ResourceCapability | None = None
    tools: ToolCapability | None = None


class Integration(ResponseModel):
    """Persisted MCP Integration metadata and its discovered catalog."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    name: str = ""
    endpoint: str = ""
    protocol_version: str | None = Field(
        default=None,
        validation_alias=AliasChoices("protocolVersion", "protocol_version"),
    )
    capabilities: IntegrationCapabilities | None = None
    server_info: dict[str, Any] | None = Field(
        default=None, validation_alias=AliasChoices("serverInfo", "server_info")
    )
    instructions: str | None = None
    status: str = ""
    last_refresh: datetime | None = Field(
        default=None, validation_alias=AliasChoices("lastRefresh", "last_refresh")
    )
    oauth_configured: bool = Field(
        default=False,
        validation_alias=AliasChoices("oauthConfigured", "oauth_configured"),
    )
    prompts: list[MCPPrompt] | None = None
    resources: list[MCPResource] | None = None
    tools: list[MCPTool] | None = None

    @property
    def catalog_included(self) -> bool:
        """Whether this response includes the complete discovered catalog."""
        return all(
            catalog is not None
            for catalog in (self.prompts, self.resources, self.tools)
        )


class OAuthCredentials(RequestModel):
    """OAuth client credentials used to configure an Integration."""

    client_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("clientId", "client_id"),
        serialization_alias="clientId",
    )
    client_secret: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("clientSecret", "client_secret"),
        serialization_alias="clientSecret",
    )

    @field_serializer("client_secret", when_used="json")
    def serialize_client_secret(self, value: SecretStr | None) -> str | None:
        """Expose the secret only when explicitly serializing a request."""
        return value.get_secret_value() if value is not None else None

    @model_validator(mode="after")
    def validate_client_credentials(self) -> OAuthCredentials:
        """Reject a client secret that cannot be associated with a client ID."""
        secret = (
            self.client_secret.get_secret_value()
            if self.client_secret is not None
            else ""
        )
        if secret.strip() and not (self.client_id or "").strip():
            raise ValueError("client_id is required when client_secret is provided")
        return self


class IntegrationCreate(RequestModel):
    """Create an Integration and optionally configure its OAuth client."""

    name: TrimmedNonEmptyString
    endpoint: _IntegrationEndpoint
    credentials: OAuthCredentials | None = None


class IntegrationUpdate(RequestModel):
    """Complete writable Integration fields used by PUT."""

    name: TrimmedNonEmptyString | None = None
    endpoint: _IntegrationEndpoint | None = None
    credentials: OAuthCredentials | None = None


class IntegrationPatch(RequestModel):
    """Partial writable Integration fields used by PATCH."""

    name: TrimmedNonEmptyString | None = None
    endpoint: _IntegrationEndpoint | None = None
    credentials: OAuthCredentials | None = None
