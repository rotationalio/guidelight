from __future__ import annotations

from ..models import Comment, CommentCreate, CommentUpdate
from .base import (
    CollectionManager,
    Page,
    decode_page,
    reference,
    request_object,
)


class Comments(CollectionManager[Comment]):
    """Manager for comments scoped to an Experiment."""

    def __init__(self, client, parent: str, parent_ref: str):
        """Create a Comment manager scoped to an Experiment."""
        super().__init__(client)
        if parent != "experiments":
            raise ValueError("comments support only experiments")
        self.path = (parent, reference(parent_ref), "comments")

    def list(self, **options) -> Page[Comment]:
        """List comments in the configured parent scope."""
        return decode_page(
            self.client.get(*self.path, query=self._query(**options)),
            key="comments",
            model=Comment,
        )

    def __iter__(self):
        """Iterate over Comments using default list options."""
        return self.iterate()

    def create(self, request=None, **fields) -> Comment:
        """Create a comment in the configured parent scope."""
        request = request_object(CommentCreate, request, fields)
        return Comment.from_dict(self.client.post(request.to_dict(), *self.path))

    def update(self, ref, request=None, **fields) -> Comment:
        """Update a comment by ID or supported reference."""
        request = request_object(CommentUpdate, request, fields)
        return Comment.from_dict(
            self.client.put(request.to_dict(), *self.path, reference(ref))
        )

    def delete(self, ref) -> None:
        """Delete a comment by ID or supported reference."""
        self.client.delete(*self.path, reference(ref))
