"""Review response models and reviewer-invitation request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .base import ResponseModel


class Review(ResponseModel):
    """A Review returned by the Endeavor API."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    experiment_id: str | None = None
    user_id: str | None = None
    status: Any = None
    user: Any = None
    completed: int = 0
    total: int = 0
    percent: float = 0.0
    progress: str = ""
