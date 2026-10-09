"""Generation response models and feedback request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import RequestModel, ResponseModel
from .testcase import TestCase


class Generation(ResponseModel):
    """A Generation returned by the Endeavor API."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    release_id: str | None = None
    experiment_id: str | None = None
    prev_id: str | None = None
    next_id: str | None = None
    title: str = ""
    error: str = ""
    context: Any = None
    prompt: list[Any] = Field(default_factory=list)
    input_modality: Any = None
    output_modality: Any = None
    output_text: str = ""
    started: datetime | None = None
    latency: int | None = None
    invocations: int | None = None
    tool_calls: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    token_usage: Any = None
    api_cost: float | None = None
    energy_cost: float | None = None
    energy_usage: Any = None
    input_attachments: list[Any] = Field(default_factory=list)
    output_attachments: list[Any] = Field(default_factory=list)
    examples: list[TestCase] = Field(default_factory=list)


class GenerationFeedback(RequestModel):
    """Scores submitted as feedback for a Generation."""

    scores: dict[str, float] = Field(min_length=1)
    generation_id: str | None = None


class GenerationTestCaseCreate(RequestModel):
    """Fields accepted when saving a Generation as a new Test Case."""

    task_ids: list[str] = Field(min_length=1)
    name: str | None = None
    from_input: bool = False


class GenerationFeedbackResponse(ResponseModel):
    """The result returned after submitting Generation feedback."""

    success: bool = False
    generation_id: str | None = None
    review_id: str | None = None
    status: str = ""
    completed: int = 0
    total: int = 0
    scores: dict[str, float] = Field(default_factory=dict)
