"""Business Aligned Objective response and request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import RequestModel, ResponseModel


class BAO(ResponseModel):
    """A Business Aligned Objective returned with an Agent."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    objectives: str = ""
    kpis: Any = None
    end_users: list[str] = Field(default_factory=list)
    sponsor: Any = None


class BAOInput(RequestModel):
    """Writable BAO fields accepted inside Agent requests."""

    objectives: str
    kpis: Any = None
    end_users: list[str] | None = None
    sponsor: Any = None
