"""Global and provider-scoped model governance manager."""

from __future__ import annotations

from typing import Any

from ..models import GovernancePolicy, GovernancePolicyCreate, GovernancePolicyPatch
from .base import (
    CollectionManager,
    Page,
    decode_page,
    reference,
    request_object,
    resolve_resource_ref,
)


class GovernancePolicies(CollectionManager[GovernancePolicy]):
    """Manage governance policies in a preserved global/provider scope."""

    valid_filters = frozenset({"active"})

    def __init__(
        self,
        client,
        provider: Any | None = None,
    ):
        """Create a global or provider-scoped governance manager."""
        super().__init__(client)
        self.provider = resolve_resource_ref(provider) if provider is not None else None

    @property
    def collection_path(self) -> tuple[str, ...]:
        """Return the configured governance collection path."""
        if self.provider is not None:
            return ("providers", self.provider, "models", "governance")
        return ("models", "governance")

    def _require_global_scope(self) -> None:
        """Reject mutations unavailable on provider-scoped governance routes."""
        if self.provider is not None:
            raise ValueError("provider-scoped governance supports listing only")

    def list(
        self, active: bool | None = None, **options: Any
    ) -> Page[GovernancePolicy]:
        """List policies while forwarding the supported active filter."""
        query = self._query(filters={"active": active}, **options)
        body = self.client.get(*self.collection_path, query=query)
        return decode_page(body, key="policies", model=GovernancePolicy)

    def __iter__(self):
        """Iterate over Governance Policies using default list options."""
        return self.iterate()

    def create(
        self, request: GovernancePolicyCreate | None = None, **fields: Any
    ) -> GovernancePolicy:
        """Create a governance policy through the global collection."""
        self._require_global_scope()
        request = request_object(GovernancePolicyCreate, request, fields)
        body = self.client.post(request.to_dict(), *self.collection_path)
        return GovernancePolicy.from_dict(body)

    def get(self, ref: Any) -> GovernancePolicy:
        """Retrieve a global governance policy by ULID."""
        self._require_global_scope()
        body = self.client.get(*self.collection_path, reference(ref))
        return GovernancePolicy.from_dict(body)

    def patch(
        self, ref: Any, request: GovernancePolicyPatch | None = None, **fields: Any
    ) -> GovernancePolicy:
        """Partially update a global governance policy."""
        self._require_global_scope()
        request = request_object(GovernancePolicyPatch, request, fields)
        body = self.client.patch(
            request.to_dict(),
            *self.collection_path,
            reference(ref),
        )
        return GovernancePolicy.from_dict(body)

    def delete(self, ref: Any) -> None:
        """Delete a global governance policy."""
        self._require_global_scope()
        self.client.delete(*self.collection_path, reference(ref))
