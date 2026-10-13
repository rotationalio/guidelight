from __future__ import annotations

from typing import Any

from ..models import Experiment, ExperimentCreate, ExperimentPatch, ExperimentUpdate
from .base import (
    Page,
    ResourceManager,
    decode_page,
    reference,
    request_object,
    resolve_resource_ref,
)
from .comments import Comments
from .reviews import Reviews
from .testcases import TestCases


class Experiments(ResourceManager):
    """Manager for the Experiment resource."""

    collection_path = ("experiments",)
    valid_filters = frozenset(
        {
            "task_ids",
            "status",
            "created_after",
            "created_before",
            "modified_after",
            "modified_before",
        }
    )

    def __init__(self, client, *, task=None):
        """Create an Experiment manager, optionally scoped to a Task."""
        super().__init__(client)
        self.task = resolve_resource_ref(task) if task is not None else None

    def list(self, **options) -> Page[Experiment]:
        """List Experiments using supported filters and pagination options."""
        if self.task is None:
            raise ValueError("Experiment listing requires a Task manager")

        filters = {
            key: options.pop(key) for key in list(options) if key in self.valid_filters
        }
        query = self._query(filters=filters, **options)
        path = (
            ("tasks", self.task, "experiments") if self.task else self.collection_path
        )
        return decode_page(
            self.client.get(*path, query=query),
            key="experiments",
            model=Experiment,
        )

    def get(self, ref) -> Experiment:
        """Retrieve an Experiment by ID or supported reference."""
        return Experiment.from_dict(
            self.client.get("experiments", resolve_resource_ref(ref))
        )

    def create(
        self,
        request: ExperimentCreate | None = None,
        **fields: Any,
    ) -> Experiment:
        """Create an Experiment under the configured Task."""
        if self.task is None:
            raise ValueError("Experiment creation requires a Task manager")
        request = request_object(ExperimentCreate, request, fields)
        body = self.client.post(request.to_dict(), "tasks", self.task, "experiments")
        return Experiment.from_dict(body)

    def update(
        self,
        ref,
        request: ExperimentUpdate | None = None,
        **fields: Any,
    ) -> Experiment:
        """Update an Experiment by ID or supported reference."""
        request = request_object(ExperimentUpdate, request, fields)
        body = self.client.put(
            request.to_dict(), "experiments", resolve_resource_ref(ref)
        )
        return Experiment.from_dict(body)

    def patch(
        self,
        ref,
        request: ExperimentPatch | None = None,
        **fields: Any,
    ) -> Experiment:
        """Partially update an Experiment by ID or supported reference."""
        request = request_object(ExperimentPatch, request, fields)
        body = self.client.patch(
            request.to_dict(), "experiments", resolve_resource_ref(ref)
        )
        return Experiment.from_dict(body)

    def delete(self, ref) -> None:
        """Delete an Experiment by ID or supported reference."""
        self.client.delete("experiments", resolve_resource_ref(ref))

    def capabilities(self, ref, capabilities: list[dict[str, Any]]) -> None:
        """Replace the capability associations for an Experiment."""
        # Endeavor binds this endpoint directly to ExperimentCapabilities and
        # returns HTTP 204 after replacing the association set.
        self.client.put(
            capabilities,
            "experiments",
            resolve_resource_ref(ref),
            "capabilities",
        )

    def test_cases(self, ref) -> TestCases:
        """Return a Test Case manager scoped to an Experiment."""
        return TestCases(self.client, experiment=resolve_resource_ref(ref))

    def set_test_cases(self, ref, version_ids: list[str]):
        """Replace the Test Case version associations for an Experiment."""
        return self.client.post(
            {"test_case_version_ids": version_ids},
            "experiments",
            reference(ref),
            "testcases",
        )

    def comments(self, ref) -> Comments:
        """Return a Comment manager scoped to an Experiment."""
        return Comments(self.client, "experiments", reference(ref))

    def reviews(self, ref) -> Reviews:
        """Return a Review manager scoped to an Experiment."""
        return Reviews(self.client, reference(ref))
