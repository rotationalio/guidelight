from __future__ import annotations

from ..models import Comment
from .base import (
    CollectionManager,
    Page,
    decode_page,
    reference,
)


class Comments(CollectionManager[Comment]):
    """Manager for comments scoped to an Experiment."""

    def __init__(self, client, parent: str, parent_ref: str):
        """Create a Comment manager scoped to an Experiment."""
        super().__init__(client)
        if parent != "experiments":
            raise ValueError("comments support only experiments")
        self.path = (parent, reference(parent_ref), "comments")

    def list(
        self,
        *,
        page_size: int | None = None,
        offset: int = 0,
        order_by: str | list[str] | None = None,
        **filters,
    ) -> Page[Comment]:
        """List comments in the configured parent scope."""
        return decode_page(
            self.client.get(
                *self.path,
                query=self._query(
                    page_size=page_size,
                    offset=offset,
                    order_by=order_by,
                    filters=filters,
                ),
            ),
            key="comments",
            model=Comment,
        )

    def __iter__(self):
        """Iterate over Comments using default list options."""
        return self.iterate()
