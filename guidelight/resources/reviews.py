from __future__ import annotations

from ..models import InviteReviewers, Review
from .base import Page, ResourceManager, decode_page, reference


class Reviews(ResourceManager):
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

    def invite(self, reviewer_ids: list[str]) -> None:
        """Invite reviewers to the configured Experiment."""
        request = InviteReviewers(
            experiment_id=self.experiment,
            reviewers=reviewer_ids,
        )
        self.client.post(request.to_dict(), "reviews", "batch")

    def delete(self, ref) -> None:
        """Delete a review by ID or supported reference."""
        self.client.delete("reviews", reference(ref))
