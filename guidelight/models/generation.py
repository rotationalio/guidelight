"""Generation response models and feedback request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import ModalityName, RequestModel, ResponseModel
from .media import Media
from .testcase import TestCase


class Generation(ResponseModel):
    """A Generation returned by the Endeavor API.

    Attachment fields are ``None`` when a response did not include them and
    lists when attachment metadata was included, including empty lists when
    none exist.
    """

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
    input_modality: list[ModalityName] = Field(default_factory=list)
    output_modality: list[ModalityName] = Field(default_factory=list)
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
    input_attachments: list[Media] | None = None
    output_attachments: list[Media] | None = None
    examples: list[TestCase] = Field(default_factory=list)

    @property
    def attachments_included(self) -> bool:
        """Report whether this response includes attachment metadata.

        Generation list responses omit attachment details even when the
        Generation has attachments. Retrieve the Generation with
        ``generations.get()`` to receive attachment metadata; empty attachment
        lists then mean that the details were included but no attachments exist.
        """
        return (
            self.input_attachments is not None and self.output_attachments is not None
        )


class GenerationTestCaseCreate(RequestModel):
    """Fields accepted when saving a Generation as a new Test Case."""

    task_ids: list[str] = Field(min_length=1)
    name: str | None = None
    from_input: bool = False
