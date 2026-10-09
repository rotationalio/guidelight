"""Task response models and writable request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import RequestModel, ResponseModel
from .metric import Metric, MetricCreate


class TaskCounts(ResponseModel):
    releases: int = 0
    experiments: int = 0
    testcases: int = 0
    metrics: int = 0


class Task(ResponseModel):
    """A Task returned by the Endeavor API."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    agent_id: str | None = None
    name: str = ""
    slug: str | None = None
    agent: str | None = None
    description: str = ""
    status: Any = None
    bao: Any = None
    counts: TaskCounts | None = None
    metrics: list[Metric] = Field(default_factory=list)
    usage: Any = None


class TaskCreate(RequestModel):
    """Writable fields accepted when creating a Task."""

    name: str
    description: str
    slug: str | None = None
    bao: Any = None
    metrics: list[MetricCreate] = Field(default_factory=list)


class TaskUpdate(RequestModel):
    """Writable fields accepted when updating a Task."""

    name: str
    description: str
    slug: str | None = None
    bao: Any = None
