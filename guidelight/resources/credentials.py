"""Provider-scoped credential resource manager."""

from __future__ import annotations

from typing import Any

from ..models import (
    ProviderCredential,
    ProviderCredentialCreate,
    ProviderCredentialPatch,
    ProviderCredentialUpdate,
    ProviderStatusResponse,
)
from .base import (
    CollectionManager,
    Page,
    decode_page,
    reference,
    request_object,
    resolve_resource_ref,
)


class ProviderCredentials(CollectionManager[ProviderCredential]):
    """Manage credentials while preserving their provider scope."""

    def __init__(self, client, provider: Any):
        """Create a credential manager scoped to one provider."""
        super().__init__(client)
        self.provider = resolve_resource_ref(provider)

    @property
    def collection_path(self) -> tuple[str, ...]:
        """Return the provider-scoped credential collection path."""
        return ("providers", self.provider, "credentials")

    def list(self, **options: Any) -> Page[ProviderCredential]:
        """List credentials for the configured provider."""
        body = self.client.get(
            *self.collection_path,
            query=self._query(**options),
        )
        return decode_page(body, key="credentials", model=ProviderCredential)

    def __iter__(self):
        """Iterate over Provider Credentials using default list options."""
        return self.iterate()

    def create(
        self, request: ProviderCredentialCreate | None = None, **fields: Any
    ) -> ProviderCredential:
        """Create a provider credential."""
        request = request_object(ProviderCredentialCreate, request, fields)
        body = self.client.post(request.to_dict(), *self.collection_path)
        return ProviderCredential.from_dict(body)

    def default(self) -> ProviderCredential:
        """Retrieve the provider's default credential metadata."""
        body = self.client.get(*self.collection_path, "default")
        return ProviderCredential.from_dict(body)

    def update(
        self, ref: Any, request: ProviderCredentialUpdate | None = None, **fields: Any
    ) -> ProviderCredential:
        """Replace provider credential metadata."""
        request = request_object(ProviderCredentialUpdate, request, fields)
        body = self.client.put(
            request.to_dict(),
            *self.collection_path,
            reference(ref),
        )
        return ProviderCredential.from_dict(body)

    def patch(
        self, ref: Any, request: ProviderCredentialPatch | None = None, **fields: Any
    ) -> ProviderCredential:
        """Partially update provider credential metadata."""
        request = request_object(ProviderCredentialPatch, request, fields)
        body = self.client.patch(
            request.to_dict(),
            *self.collection_path,
            reference(ref),
        )
        return ProviderCredential.from_dict(body)

    def delete(self, ref: Any) -> None:
        """Delete a provider credential."""
        self.client.delete(*self.collection_path, reference(ref))

    def test_connectivity(self, secret_ref: Any) -> ProviderStatusResponse:
        """Test connectivity using a provider credential."""
        body = self.client.get(
            *self.collection_path,
            reference(secret_ref),
            "test-connectivity",
        )
        return ProviderStatusResponse.from_dict(body)
