"""Agent response models and writable request types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .bao import BAO, BAOInput
from .base import ResponseModel, parse_datetime, serialize_value

@dataclass
class AgentInfo(ResponseModel):
    """Read-only aggregate information returned for an Agent."""

    task_count: int | None = None
    deployed_task_count: int | None = None
    token_count: int | None = None
    total_cost: float | None = None
    _extra: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentInfo":
        known = {
            "task_count",
            "deployed_task_count",
            "token_count",
            "total_cost",
        }
        return cls(
            task_count=data.get("task_count"),
            deployed_task_count=data.get("deployed_task_count"),
            token_count=data.get("token_count"),
            total_cost=data.get("total_cost"),
            _extra={key: value for key, value in data.items() if key not in known},
        )


@dataclass
class Agent(ResponseModel):
    """An Agent returned by the Endeavor API."""

    id: str | None = None
    created: Any = None
    modified: Any = None
    name: str = ""
    slug: str | None = None
    description: str = ""
    bao: BAO | None = None
    usage: Any = None
    info: AgentInfo | None = None
    _extra: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Agent":
        known = {
            "id",
            "created",
            "modified",
            "name",
            "slug",
            "description",
            "bao",
            "usage",
            "info",
        }
        bao = data.get("bao")
        info = data.get("info")
        return cls(
            id=data.get("id"),
            created=parse_datetime(data.get("created")),
            modified=parse_datetime(data.get("modified")),
            name=data.get("name", ""),
            slug=data.get("slug"),
            description=data.get("description", ""),
            bao=BAO.from_dict(bao) if isinstance(bao, dict) else None,
            usage=data.get("usage"),
            info=AgentInfo.from_dict(info) if isinstance(info, dict) else None,
            _extra={key: value for key, value in data.items() if key not in known},
        )


@dataclass
class AgentCreate:
    """Writable fields accepted by POST /v2/agents."""

    name: str
    description: str
    bao: BAOInput | None = None

    def to_dict(self) -> dict[str, Any]:
        values = {
            "name": self.name,
            "description": self.description,
            "bao": self.bao,
        }
        return {
            key: serialize_value(value)
            for key, value in values.items()
            if value is not None
        }


@dataclass
class AgentUpdate:
    """Writable fields accepted by PUT /v2/agents/{id}."""

    name: str
    description: str
    bao: BAOInput | None = None

    def to_dict(self) -> dict[str, Any]:
        values = {
            "name": self.name,
            "description": self.description,
            "bao": self.bao,
        }
        return {
            key: serialize_value(value)
            for key, value in values.items()
            if value is not None
        }
