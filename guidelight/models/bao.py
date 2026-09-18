"""Business Aligned Objective response and request types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import ResponseModel, parse_datetime, serialize_value


@dataclass
class BAO(ResponseModel):
    """A Business Aligned Objective returned with an Agent."""

    id: str | None = None
    created: Any = None
    modified: Any = None
    objectives: str = ""
    kpis: Any = None
    end_users: list[str] = field(default_factory=list)
    sponsor: Any = None
    _extra: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BAO":
        known = {
            "id",
            "created",
            "modified",
            "objectives",
            "kpis",
            "end_users",
            "sponsor",
        }
        return cls(
            id=data.get("id"),
            created=parse_datetime(data.get("created")),
            modified=parse_datetime(data.get("modified")),
            objectives=data.get("objectives", ""),
            kpis=data.get("kpis"),
            end_users=list(data.get("end_users") or []),
            sponsor=data.get("sponsor"),
            _extra={key: value for key, value in data.items() if key not in known},
        )


@dataclass
class BAOInput:
    """Writable BAO fields accepted inside Agent create/update requests."""

    objectives: str
    kpis: Any = None
    end_users: list[str] | None = None
    sponsor: Any = None

    def to_dict(self) -> dict[str, Any]:
        values = {
            "objectives": self.objectives,
            "kpis": self.kpis,
            "end_users": self.end_users,
            "sponsor": self.sponsor,
        }
        return {
            key: serialize_value(value)
            for key, value in values.items()
            if value is not None
        }
