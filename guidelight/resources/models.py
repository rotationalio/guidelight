"""Read-only model catalog manager."""

from __future__ import annotations

from typing import Any

from ..models import Model, ModelUsage
from .base import (
    CollectionManager,
    Page,
    decode_page,
    reference,
    resolve_resource_ref,
)


class Models(CollectionManager[Model]):
    """Browse the read-only model catalog."""

    valid_filters = frozenset(
        {
            "restricted",
            "provider_id",
            "author",
            "published_after",
            "published_before",
            "input_modality",
            "output_modality",
            "context_size_above",
            "capabilities",
            "input_cost_limit",
            "output_cost_limit",
            "tpm_limit",
            "rpm_limit",
            "is_moderated",
            "api_type",
            "auth_type",
            "selected_model_id",
        }
    )

    def __init__(self, client, provider: str | None = None):
        """Create a global or provider-scoped model catalog manager."""
        super().__init__(client)
        self.provider = resolve_resource_ref(provider) if provider is not None else None

    @property
    def collection_path(self) -> tuple[str, ...]:
        """Return the global or provider-scoped model route."""
        if self.provider is None:
            return ("models",)
        return ("providers", self.provider, "models")

    def list(self, **filters: Any) -> Page[Model]:
        """List catalog models using supported model filters."""
        query = self._query(**filters)
        body = self.client.get(*self.collection_path, query=query)
        return decode_page(body, key="models", model=Model)

    def __iter__(self):
        """Iterate over Models using default list options."""
        return self.iterate()

    def get(self, ref: Any) -> Model:
        """Retrieve a catalog model by ULID."""
        body = self.client.get("models", reference(ref))
        return Model.from_dict(body)

    def usage(self, ref: Any) -> ModelUsage:
        """Retrieve usage and deployment counts for a model."""
        body = self.client.get("models", reference(ref), "usage")
        return ModelUsage.from_dict(body)
