"""Agent response models and writable request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .bao import BAO, BAOInput
from .base import RequestModel, ResponseModel


class AgentInfo(ResponseModel):
    """Read-only aggregate information returned for an Agent."""

    task_count: int | None = None
    deployed_task_count: int | None = None
    token_count: int | None = None
    total_cost: float | None = None


class Agent(ResponseModel):
    """An Agent returned by the Endeavor API."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    name: str = ""
    slug: str | None = None
    description: str = ""
    bao: BAO | None = None
    usage: Any = None
    info: AgentInfo | None = None


class AgentCreate(RequestModel):
    """Writable fields accepted by POST /v2/agents."""

    name: str
    description: str
    bao: BAOInput | None = None


class AgentUpdate(RequestModel):
    """Writable fields accepted by PUT /v2/agents/{id}."""

    name: str
    description: str
    bao: BAOInput | None = None
