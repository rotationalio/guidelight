"""Metric response models and writable request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import RequestModel, ResponseModel


class MetricOption(ResponseModel):
    label: str
    value: float
    icon: str | None = None


class Metric(ResponseModel):
    """A Metric returned by the Endeavor API."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    name: str = ""
    slug: str | None = None
    description: str = ""
    scoring: Any = None
    icon: str | None = None
    widget: Any = None
    options: list[MetricOption] = Field(default_factory=list)
    max_score: float | None = None
    min_score: float | None = None
    step: float | None = None
    system: bool = False
    value: float | None = None


class MetricCreate(RequestModel):
    """Writable fields accepted when creating a Metric."""

    name: str
    description: str = ""
    slug: str | None = None
    scoring: str = Field(min_length=1)
    widget: Any = None
    options: list[dict[str, Any]] = Field(default_factory=list)
    max_score: float | None = None
    min_score: float | None = None
    step: float | None = None


class MetricUpdate(RequestModel):
    """Writable fields accepted when updating a Metric."""

    name: str
    description: str = ""
    slug: str | None = None
    scoring: str = Field(min_length=1)
    widget: Any = None
    options: list[dict[str, Any]] = Field(default_factory=list)
    max_score: float | None = None
    min_score: float | None = None
    step: float | None = None
