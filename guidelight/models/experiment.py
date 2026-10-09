"""Experiment response models and writable request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .base import RequestModel, ResponseModel

ExperimentStatus = Literal[
    "unknown",
    "draft",
    "ready",
    "active",
    "review",
    "completed",
    "error",
    "archived",
]


ModalityName = Literal[
    "Text",
    "Image",
    "Audio",
    "Video",
    "Document",
    "Spatial",
    "TimeSeries",
    "Robotic",
    "Genomic",
]

RendererName = Literal["sprintf", "jinja", "go"]
ExperimentRendererName = Literal["unknown", "sprintf", "jinja", "go"]


class Experiment(ResponseModel):
    """An Experiment returned by the Endeavor API."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    name: str = ""
    slug: str | None = None
    description: str = ""
    status: ExperimentStatus | None = None
    context_type: str | None = None
    input_types: list[str] = Field(default_factory=list)
    input_modality: list[ModalityName] = Field(default_factory=list)
    output_types: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any] | None = None
    output_modality: list[ModalityName] = Field(default_factory=list)
    output_schema: dict[str, Any] | None = None
    model_id: str | None = None
    model_name: str | None = None
    renderer: ExperimentRendererName | None = None
    prompts: list[Any] = Field(default_factory=list)
    parameters: Any = None
    usage: Any = None
    info: dict[str, Any] | None = None
    capabilities: list[dict[str, Any]] | None = None

    @field_validator(
        "input_types",
        "input_modality",
        "output_types",
        "output_modality",
        "prompts",
        mode="before",
    )
    @classmethod
    def normalize_nullable_lists(cls, value: Any) -> Any:
        """Normalize nullable list fields returned for draft Experiments."""
        return [] if value is None else value


class ExperimentCreate(RequestModel):
    """Writable fields accepted when creating an Experiment."""

    name: str | None = None
    slug: str | None = None
    description: str | None = None
    status: Literal["ready"] | None = None
    context_type: str | None = None
    input_types: list[str] | None = None
    input_modality: list[ModalityName] | None = None
    output_types: list[str] | None = None
    output_modality: list[ModalityName] | None = None
    model_id: str | None = None
    renderer: RendererName | None = None
    prompts: list[Any] | None = None
    parameters: Any = None
    capabilities: list[dict[str, Any]] | None = None


class ExperimentUpdate(RequestModel):
    """Writable fields accepted when updating an Experiment."""

    name: str
    slug: str | None = None
    description: str = ""
    status: Literal["ready"] | None = None
    context_type: str | None = None
    input_types: list[str] = Field(default_factory=list)
    input_modality: list[ModalityName] = Field(min_length=1)
    output_types: list[str] = Field(min_length=1)
    output_modality: list[ModalityName] = Field(min_length=1)
    model_id: str | None = None
    renderer: RendererName
    prompts: list[Any] = Field(min_length=1)
    parameters: Any = None
    capabilities: list[dict[str, Any]] | None = None

    @model_validator(mode="after")
    def validate_text_input(self) -> ExperimentUpdate:
        if "Text" in self.input_modality:
            if not self.context_type:
                raise ValueError("context_type is required for text input")
            if not self.input_types:
                raise ValueError("input_types must not be empty for text input")
        return self


class ExperimentPatch(RequestModel):
    """Partially update an Experiment.

    Draft Experiments may update their configuration or transition to ready.
    Non-draft Experiments may update only their name, slug, and description.
    """

    name: str | None = None
    slug: str | None = None
    description: str | None = None
    status: Literal["ready"] | None = None
    context_type: str | None = None
    input_types: list[str] | None = None
    input_modality: list[ModalityName] | None = None
    output_types: list[str] | None = None
    output_modality: list[ModalityName] | None = None
    model_id: str | None = None
    renderer: RendererName | None = None
    prompts: list[Any] | None = None
    parameters: Any = None
    capabilities: list[dict[str, Any]] | None = None
