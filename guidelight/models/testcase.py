"""Test Case response models and writable request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import RequestModel, ResponseModel


class TestCaseAttachment(ResponseModel):
    """Attachment metadata associated with a Test Case version."""

    id: str | None = None
    name: str = ""
    description: str = ""
    url: str = ""
    content_type: Any = None
    created: datetime | None = None


class TestCaseVersion(ResponseModel):
    """A versioned Test Case input and its attachments."""

    id: str | None = None
    version: int = 0
    context: Any = None
    context_type: Any = None
    input_modality: Any = None
    created: datetime | None = None
    selected: bool = False
    attachments: list[TestCaseAttachment] = Field(default_factory=list)


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


class TestCaseCreate(RequestModel):
    """Writable fields accepted when creating a Test Case."""

    title: str
    description: str = ""
    context: str | None = None
    context_json: Any = None
    context_type: Any = None
    input_modality: Any = None
    attachments: list[str] = Field(default_factory=list)
    task_id: str | None = None
    experiment_id: str | None = None


class TestCaseUpdate(RequestModel):
    """Writable fields accepted when updating a Test Case."""

    title: str
    description: str = ""
    context: str | None = None
    context_json: Any = None
    context_type: Any = None
    input_modality: Any = None
    attachments: list[str] = Field(default_factory=list)
