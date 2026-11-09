"""Typed deployed-Task execution responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, Field, field_validator

from .base import ResponseModel


class ExecutionUsage(ResponseModel):
    """Usage reported for a deployed Task execution."""

    invocations: int = 0
    tool_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    api_cost: float = 0.0
    energy_cost: float = 0.0


class ExecutionModel(ResponseModel):
    """Model configuration used for a deployed Task execution."""

    slug: str = ""
    parameters: dict[str, Any] | None = None


class ExecutionAttachment(ResponseModel):
    """File returned directly by a deployed Task execution."""

    id: str | None = None
    filename: str
    content_type: str = ""
    url: str = ""
    data: bytes | None = Field(default=None, repr=False)


class ExecutionResult(ResponseModel):
    """A typed execution output returned by a deployed Task.

    Args:
        usage: Model and capability usage for the execution.
        model: Model configuration used for the execution.
        output: Final or partial model output.
        mime_type: Media type of the model output.
        capabilities: Capabilities enabled for the execution.
        actions: Action log emitted by the execution.
        started: Time at which execution started.
        finished: Time at which execution finished.
        outcome: Terminal execution outcome.
        attachments: Files returned with a multipart response.
        raw_response: Original JSON output envelope.
    """

    usage: ExecutionUsage
    model: ExecutionModel
    output: Any = None
    mime_type: str = ""
    capabilities: list[str] = Field(default_factory=list)
    actions: Any = None
    started: datetime | None = None
    finished: datetime | None = None
    outcome: Literal["succeeded", "failed", "cancelled"]
    attachments: list[ExecutionAttachment] = Field(
        default_factory=list,
        validation_alias=AliasChoices("attachments", "Attachments"),
    )
    raw_response: Any = None

    @field_validator("capabilities", "attachments", mode="before")
    @classmethod
    def normalize_optional_collections(cls, value):
        """Convert null execution collections to empty lists."""
        return [] if value is None else value
