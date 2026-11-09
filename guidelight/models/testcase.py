"""Test Case response models and writable request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .base import ModalityName, RequestModel, ResponseModel, TrimmedNonEmptyString
from .media import Media

PromptRole = Literal[
    "user",
    "system",
    "developer",
    "assistant",
    "tool",
    "function",
]

PromptRenderer = Literal["sprintf", "go"]


class TestCaseVersion(ResponseModel):
    """A versioned Test Case input and its attachments."""

    id: str | None = None
    version: int = 0
    context: Any = None
    context_type: str | None = None
    input_modality: list[ModalityName] = Field(default_factory=list)
    created: datetime | None = None
    selected: bool = False
    attachments: list[Media] = Field(default_factory=list)


class TestCaseVersionURL(ResponseModel):
    version: int
    url: str


class TestCase(ResponseModel):
    """A Test Case returned by the Endeavor API."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    title: str = ""
    description: str = ""
    golden_example: str | None = None
    versions: list[TestCaseVersionURL] = Field(default_factory=list)
    latest: TestCaseVersion | None = None
    selected: bool = False
    has_golden: bool = False


class TestCaseArchiveUploadResponse(ResponseModel):
    """Count returned after importing a Test Case archive."""

    testcases: int = 0


class TestCaseCreate(RequestModel):
    """Writable fields accepted when creating a Test Case."""

    title: str
    description: str = ""
    context: str | None = None
    context_json: Any = None
    context_type: str | None = None
    input_modality: list[ModalityName] | None = None
    attachments: list[str] = Field(default_factory=list)
    task_id: str | None = None
    experiment_id: str | None = None


class TestCaseUpdate(RequestModel):
    """Writable fields accepted when updating a Test Case."""

    title: str
    description: str = ""
    context: str | None = None
    context_json: Any = None
    context_type: str | None = None
    input_modality: list[ModalityName] | None = None
    attachments: list[str] = Field(default_factory=list)


class TestCaseArchiveRequest(RequestModel):
    """Select exactly one Test Case collection to download."""

    agent: TrimmedNonEmptyString | None = None
    task: TrimmedNonEmptyString | None = None
    experiment: TrimmedNonEmptyString | None = None
    testcases: list[TrimmedNonEmptyString] | None = Field(
        default=None,
        min_length=1,
    )

    @model_validator(mode="after")
    def require_one_selector(self) -> TestCaseArchiveRequest:
        """Require exactly one archive selector."""
        selectors = (self.agent, self.task, self.experiment, self.testcases)
        if sum(selector is not None for selector in selectors) != 1:
            raise ValueError(
                "exactly one of agent, task, experiment, or testcases is required"
            )
        return self


class PromptTemplate(RequestModel):
    """A prompt template accepted by Endeavor's render endpoint."""

    index: int = Field(ge=0)
    role: PromptRole
    template: str


class PromptRenderRequest(RequestModel):
    """Input accepted by the Test Case prompt-render endpoint.

    Args:
        renderer: Template renderer to use.
        prompts: Prompt templates to render with the Test Case context.
    """

    renderer: PromptRenderer
    prompts: list[PromptTemplate] = Field(min_length=1)


class RenderedMessage(ResponseModel):
    """One rendered prompt message returned by Endeavor."""

    role: PromptRole
    content: str


class RenderedPrompt(ResponseModel):
    """Rendered messages or a template error returned by Endeavor."""

    messages: list[RenderedMessage] = Field(default_factory=list)
    renderer: PromptRenderer | Literal["unknown"] = "unknown"
    error: str = ""

    @field_validator("messages", mode="before")
    @classmethod
    def normalize_messages(cls, value):
        """Normalize Endeavor's null error-response messages to an empty list."""
        return [] if value is None else value
