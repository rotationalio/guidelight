from __future__ import annotations

from ..models import (
    Generation,
    Release,
    ReleaseClone,
    ReleaseCreate,
    ReleasePatch,
    ReleaseTest,
    ReleaseTestResult,
    ReleaseUpdate,
)
from .base import (
    Page,
    ResourceManager,
    decode_many,
    decode_page,
    request_object,
    resolve_resource_ref,
    reference,
)


class Releases(ResourceManager):
    """Manager for the Release resource."""

    collection_path = ("releases",)
    valid_filters = frozenset(
        {
            "task_id",
            "environment_id",
            "experiment_id",
            "task_ids",
            "environment_ids",
            "experiment_ids",
            "version",
            "version_min",
            "version_max",
            "created_after",
            "created_before",
            "modified_after",
            "modified_before",
            "deployed",
            "deployed_after",
            "deployed_before",
            "retired",
            "retired_after",
            "retired_before",
        }
    )

    def __init__(self, client, *, task=None):
        """Create a Release manager, optionally scoped to a Task."""
        super().__init__(client)
        self.task = resolve_resource_ref(task) if task is not None else None

    def list(self, **options) -> Page[Release]:
        """List Releases using supported filters and pagination options."""
        filters = {
            key: options.pop(key) for key in list(options) if key in self.valid_filters
        }
        query = self._query(filters=filters, **options)
        path = ("tasks", self.task, "releases") if self.task else self.collection_path
        return decode_page(
            self.client.get(*path, query=query),
            key="releases",
            model=Release,
        )

    def get(self, ref) -> Release:
        """Retrieve a Release by ID or supported reference."""
        return Release.from_dict(self.client.get("releases", reference(ref)))

    def create(self, request=None, **fields) -> list[Release]:
        """Create Releases and decode the multi-release response envelope."""
        request = request_object(ReleaseCreate, request, fields)
        path = ("tasks", self.task, "releases") if self.task else self.collection_path
        body = self.client.post(request.to_dict(), *path)
        return decode_many(body, key="releases", model=Release)

    def update(self, ref, request=None, **fields) -> Release:
        """Update a Release by ID or supported reference."""
        request = request_object(ReleaseUpdate, request, fields)
        return Release.from_dict(
            self.client.put(request.to_dict(), "releases", reference(ref))
        )

    def patch(self, ref, request=None, **fields) -> Release:
        """Partially update a Release by ID or supported reference."""
        request = request_object(ReleasePatch, request, fields)
        return Release.from_dict(
            self.client.patch(request.to_dict(), "releases", reference(ref))
        )

    def delete(self, ref) -> None:
        """Delete a Release by ID or supported reference."""
        self.client.delete("releases", reference(ref))

    def clone(self, ref, environments: list[str]) -> list[Release]:
        """Clone a Release into the requested environments."""
        body = self.client.post(
            ReleaseClone(environments=environments).to_dict(),
            "releases",
            reference(ref),
            "clone",
        )
        return decode_many(body, key="releases", model=Release)

    def deploy(self, ref) -> Release:
        """Deploy a Release by ID or supported reference."""
        return Release.from_dict(
            self.client.post({}, "releases", reference(ref), "deploy")
        )

    def retire(self, ref) -> Release:
        """Retire a Release by ID or supported reference."""
        return Release.from_dict(
            self.client.post({}, "releases", reference(ref), "retire")
        )

    def test(self, ref, request=None, **fields) -> ReleaseTestResult:
        """Execute a test request against a Release."""
        request = request_object(ReleaseTest, request, fields)
        body = self.client.post(request.to_dict(), "releases", reference(ref), "test")
        return ReleaseTestResult.from_dict(body)

    def generations(self, ref) -> ReleaseGenerations:
        """Return a Generation manager scoped to a Release."""
        return ReleaseGenerations(self.client, ref)


class ReleaseGenerations(ResourceManager):
    """Manager for Generations scoped to one Release."""

    def __init__(self, client, release: str):
        """Create a Generation manager scoped to a Release."""
        super().__init__(client)
        self.release = reference(release)

    def list(self, **options) -> Page[Generation]:
        """List Generations for the configured Release."""
        body = self.client.get(
            "releases",
            self.release,
            "generations",
            query=self._query(**options),
        )
        return decode_page(body, key="generations", model=Generation)
