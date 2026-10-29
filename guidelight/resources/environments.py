"""Environment resource manager."""

from __future__ import annotations

from typing import Any

from ..models import Environment, EnvironmentCreate, EnvironmentPatch, EnvironmentUpdate
from .base import CollectionManager, Page, decode_page, reference, request_object


class Environments(CollectionManager[Environment]):
    """Manage global deployment environments."""

    collection_path = ("environments",)
    valid_filters = frozenset({"provider_id"})

    def list(self, provider_id: str | None = None, **options: Any) -> Page[Environment]:
        """List environments, optionally filtered by provider."""
        query = self._query(filters={"provider_id": provider_id}, **options)
        body = self.client.get(*self.collection_path, query=query)
        return decode_page(body, key="environments", model=Environment)

    def __iter__(self):
        """Iterate over Environments using default list options."""
        return self.iterate()

    def create(self, request: EnvironmentCreate | None = None, **fields: Any):
        """Create an environment."""
        request = request_object(EnvironmentCreate, request, fields)
        body = self.client.post(request.to_dict(), *self.collection_path)
        return Environment.from_dict(body)

    def get(self, ref: Any) -> Environment:
        """Retrieve an environment by ULID."""
        return Environment.from_dict(self.client.get("environments", reference(ref)))

    def update(
        self, ref: Any, request: EnvironmentUpdate | None = None, **fields: Any
    ) -> Environment:
        """Replace an environment."""
        request = request_object(EnvironmentUpdate, request, fields)
        body = self.client.put(request.to_dict(), "environments", reference(ref))
        return Environment.from_dict(body)

    def patch(
        self, ref: Any, request: EnvironmentPatch | None = None, **fields: Any
    ) -> Environment:
        """Partially update an environment."""
        request = request_object(EnvironmentPatch, request, fields)
        body = self.client.patch(request.to_dict(), "environments", reference(ref))
        return Environment.from_dict(body)

    def delete(self, ref: Any) -> None:
        """Delete an environment."""
        self.client.delete("environments", reference(ref))
