from __future__ import annotations
from ..models import Metric, MetricCreate, MetricUpdate
from .base import (
    Page,
    ResourceManager,
    decode_page,
    request_object,
    resolve_resource_ref,
)


class Metrics(ResourceManager):
    """Manager for Metrics scoped to one Task."""

    def __init__(self, client, task):
        """Create a Metric manager scoped to a Task."""
        super().__init__(client)
        self.task = resolve_resource_ref(task)

    @property
    def collection_path(self):
        """Return the Task-scoped Metric collection path."""
        return ("tasks", self.task, "metrics")

    def list(self, **options) -> Page[Metric]:
        """List Metrics using pagination and filter options."""
        return decode_page(
            self.client.get(*self.collection_path, query=self._query(**options)),
            key="metrics",
            model=Metric,
        )

    def create(self, request=None, **fields) -> Metric:
        """Create a Metric under the configured Task."""
        request = request_object(MetricCreate, request, fields)
        return Metric.from_dict(
            self.client.post(request.to_dict(), *self.collection_path)
        )

    def get(self, ref) -> Metric:
        """Retrieve a Metric by ID or supported reference."""
        return Metric.from_dict(self.client.get("metrics", resolve_resource_ref(ref)))

    def update(self, ref, request=None, **fields) -> Metric:
        """Update a Metric by ID or supported reference."""
        request = request_object(MetricUpdate, request, fields)
        return Metric.from_dict(
            self.client.put(request.to_dict(), "metrics", resolve_resource_ref(ref))
        )

    def delete(self, ref) -> None:
        """Delete a Metric by ID or supported reference."""
        self.client.delete("metrics", resolve_resource_ref(ref))
