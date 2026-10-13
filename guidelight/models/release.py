"""Release response models and lifecycle request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from .base import RequestModel, ResponseModel
from .experiment import Experiment
from .task import Task


class Release(ResponseModel):
    """A Release returned by the Endeavor API."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    task_id: str | None = None
    experiment_id: str | None = None
    environment_id: str | None = None
    provider_id: str | None = None
    version: str = ""
    status: str = ""
    deployed_on: datetime | None = None
    is_deployed: bool = False
    retired_on: datetime | None = None
    is_retired: bool = False
    task: Task | None = None
    experiment: Experiment | None = None
    environment: Any = None
    endpoint: str | None = None


class ReleaseCreate(RequestModel):
    """Writable fields accepted when creating Releases."""

    experiment_id: str
    environments: list[str] = Field(min_length=1)
    version: str
    task_id: str | None = None


class ReleaseUpdate(RequestModel):
    """Writable deployment metadata accepted when updating a Release."""

    provider_id: str | None = None
    deployed_on: datetime | None = None
    retired_on: datetime | None = None


class ReleasePatch(ReleaseUpdate):
    """Writable deployment metadata accepted by a Release PATCH."""

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> ReleasePatch:
        """Require at least one mutable field."""
        if (
            self.provider_id is None
            and self.deployed_on is None
            and self.retired_on is None
        ):
            raise ValueError("at least one mutable Release field is required")
        return self


class ReleaseClone(RequestModel):
    """Destination environments accepted when cloning a Release."""

    environments: list[str] = Field(min_length=1)


class ReleaseTest(RequestModel):
    """Input context accepted when testing a Release."""

    input: str


class ReleaseTestResult(ResponseModel):
    """Output returned after testing a Release."""

    output_text: str = ""
    error: str = ""
