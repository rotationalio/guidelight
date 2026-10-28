"""Provider resource manager and provider-scoped manager factories."""

from __future__ import annotations

from typing import Any

from ..models import (
    Provider,
    ProviderCreate,
    ProviderPatch,
    ProviderStatusResponse,
    ProviderUpdate,
)
from .base import (
    CollectionManager,
    Page,
    decode_page,
    request_object,
    resolve_resource_ref,
)
from .credentials import ProviderCredentials
from .governance import GovernancePolicies
from .models import Models


class Providers(CollectionManager[Provider]):
    """Manage providers and their provider-scoped resources."""

    collection_path = ("providers",)
    valid_filters = frozenset()

    def list(self, **options: Any) -> Page[Provider]:
        """List configured providers."""
        query = self._query(**options)
        body = self.client.get(*self.collection_path, query=query)
        return decode_page(body, key="providers", model=Provider)

    def __iter__(self):
        """Iterate over Providers using default list options."""
        return self.iterate()

    def create(self, request: ProviderCreate | None = None, **fields: Any) -> Provider:
        """Create a provider."""
        request = request_object(ProviderCreate, request, fields)
        body = self.client.post(request.to_dict(), *self.collection_path)
        return Provider.from_dict(body)

    def get(self, ref: Any) -> Provider:
        """Retrieve a provider by ULID or slug."""
        return Provider.from_dict(
            self.client.get("providers", resolve_resource_ref(ref))
        )

    def update(
        self, ref: Any, request: ProviderUpdate | None = None, **fields: Any
    ) -> Provider:
        """Replace a provider."""
        request = request_object(ProviderUpdate, request, fields)
        body = self.client.put(
            request.to_dict(),
            "providers",
            resolve_resource_ref(ref),
        )
        return Provider.from_dict(body)

    def patch(
        self, ref: Any, request: ProviderPatch | None = None, **fields: Any
    ) -> Provider:
        """Partially update a provider."""
        request = request_object(ProviderPatch, request, fields)
        body = self.client.patch(
            request.to_dict(),
            "providers",
            resolve_resource_ref(ref),
        )
        return Provider.from_dict(body)

    def delete(self, ref: Any) -> None:
        """Delete a provider."""
        self.client.delete("providers", resolve_resource_ref(ref))

    def default(self) -> Provider:
        """Retrieve the configured default provider."""
        return Provider.from_dict(self.client.get("providers", "default"))

    def test_connectivity(self, ref: Any) -> ProviderStatusResponse:
        """Test connectivity to a provider."""
        body = self.client.get(
            "providers",
            resolve_resource_ref(ref),
            "test-connectivity",
        )
        return ProviderStatusResponse.from_dict(body)

    def refresh_catalog(self, ref: Any) -> None:
        """Request a provider catalog refresh."""
        self.client.post(
            {},
            "providers",
            resolve_resource_ref(ref),
            "refresh-catalog",
        )

    def update_status(self, ref: Any, status: str) -> None:
        """Apply the provider status action."""
        self.client.patch(
            {},
            "providers",
            resolve_resource_ref(ref),
            "status",
            status,
        )

    def models(self, ref: Any) -> Models:
        """Return a model manager scoped to a provider."""
        return Models(self.client, provider=resolve_resource_ref(ref))

    def credentials(self, ref: Any) -> ProviderCredentials:
        """Return a credential manager scoped to a provider."""
        return ProviderCredentials(
            self.client,
            provider=resolve_resource_ref(ref),
        )

    def governance(self, ref: Any) -> GovernancePolicies:
        """Return a governance manager scoped to a provider."""
        return GovernancePolicies(
            self.client,
            provider=resolve_resource_ref(ref),
        )
