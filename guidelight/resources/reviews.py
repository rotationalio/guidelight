from __future__ import annotations

from ..models import Review
from .base import CollectionManager, Page, decode_page, reference


class Reviews(CollectionManager[Review]):
    """Manager for reviews scoped to one Experiment."""

    def __init__(self, client, experiment):
        """Create a Review manager scoped to an Experiment."""
        super().__init__(client)
        self.experiment = reference(experiment)

    def list(self, **options) -> Page[Review]:
        """List reviews for the configured Experiment."""
        body = self.client.get(
            "experiments",
            self.experiment,
            "reviews",
            query=self._query(**options),
        )
        return decode_page(body, key="reviews", model=Review)

    def __iter__(self):
        """Iterate over Reviews using default list options."""
        return self.iterate()

    def delete(self, ref) -> None:
        """Delete a review by ID or supported reference."""
        self.client.delete("reviews", reference(ref))
