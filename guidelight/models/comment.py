"""Comment response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import ResponseModel


class Comment(ResponseModel):
    """A Comment returned by the Endeavor API."""

    id: str | None = None
    created: datetime | None = None
    modified: datetime | None = None
    object_url: str | None = None
    rendered_content: str | None = None
    content: str = ""
    reply_to: str | None = None
    user: Any = None
    replies: list[Comment] = Field(default_factory=list)
