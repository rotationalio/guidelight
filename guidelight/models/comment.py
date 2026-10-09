"""Comment response models and writable request types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import RequestModel, ResponseModel


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


class CommentCreate(RequestModel):
    """Writable fields accepted when creating a Comment."""

    content: str
    reply_to: str | None = None


class CommentUpdate(RequestModel):
    """Writable fields accepted when updating a Comment."""

    content: str
