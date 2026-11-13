from __future__ import annotations

import time
import warnings
from typing import Any

from ..exceptions import (
    IntegrationAuthorizationRequired,
    IntegrationPendingWarning,
    IntegrationRegistrationRequired,
    IntegrationStatusError,
    IntegrationStatusTimeout,
)
from ..models import (
    Integration,
    IntegrationCreate,
    IntegrationPatch,
    IntegrationUpdate,
)
from .base import CollectionManager, Page, decode_page, reference, request_object


class Integrations(CollectionManager[Integration]):
    """Manage API-subject-compatible MCP Integrations."""

    collection_path = ("integrations",)
    valid_filters = frozenset()

    def list(
        self,
        *,
        page_size: int | None = None,
        offset: int = 0,
        order_by: str | list[str] | None = None,
        **filters: Any,
    ) -> Page[Integration]:
        query = self._query(
            page_size=page_size,
            offset=offset,
            order_by=order_by,
            filters=filters,
        )
        return decode_page(
            self.client.get(*self.collection_path, query=query),
            key="integrations",
            model=Integration,
        )

    def __iter__(self):
        """Iterate over Integrations using default list options."""
        return self.iterate()

    def get(self, ref: Any) -> Integration:
        """Retrieve an Integration by model or ULID."""
        integration = Integration.from_dict(
            self.client.get("integrations", reference(ref))
        )
        return integration.model_copy(
            update={
                "prompts": integration.prompts or [],
                "resources": integration.resources or [],
                "tools": integration.tools or [],
            }
        )

    def create(
        self,
        request: IntegrationCreate | None = None,
        *,
        wait: bool = False,
        timeout: float = 120,
        initial_delay: float = 2,
        max_delay: float = 16,
        **fields: Any,
    ) -> Integration:
        """Create an Integration and optionally wait for discovery.

        ``create`` returns immediately for pending Integrations unless
        ``wait=True``. Authorization and registration requirements emit
        warnings and remain eligible for polling when ``wait=True``.
        Other terminal configuration states raise a descriptive SDK
        exception.
        """
        request = request_object(IntegrationCreate, request, fields)
        integration = Integration.from_dict(
            self.client.post(request.to_dict(), *self.collection_path)
        )
        self._raise_for_status(integration, notify_pending=True)
        if wait:
            if not integration.id:
                raise ValueError("created Integration did not include an ID")
            return self.wait_for_status(
                integration.id,
                timeout=timeout,
                initial_delay=initial_delay,
                max_delay=max_delay,
            )
        return integration

    def wait_for_status(
        self,
        ref: Any,
        *,
        timeout: float = 120,
        initial_delay: float = 2,
        max_delay: float = 16,
    ) -> Integration:
        """Poll an Integration until it connects or reaches a terminal state.

        Authorization and registration statuses emit warnings and continue
        polling, allowing the caller to complete setup while this method
        waits.
        """
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if initial_delay <= 0 or max_delay <= 0:
            raise ValueError("poll delays must be positive")
        if initial_delay > max_delay:
            raise ValueError("initial_delay must not exceed max_delay")

        integration_ref = reference(ref)
        integration = self.get(integration_ref)
        deadline = time.monotonic() + timeout
        delay = initial_delay
        while True:
            self._raise_for_status(integration)
            if integration.status == "connected":
                return integration
            if time.monotonic() >= deadline:
                raise IntegrationStatusTimeout(
                    integration.id or integration_ref,
                    integration.status,
                    timeout,
                )
            time.sleep(min(delay, max(0, deadline - time.monotonic())))
            integration = self.get(integration_ref)
            delay = min(delay * 2, max_delay)

    def _raise_for_status(
        self,
        integration: Integration,
        *,
        notify_pending: bool = False,
    ) -> None:
        """Raise a descriptive exception for terminal non-success states."""
        if integration.status == "pending":
            if notify_pending:
                warnings.warn(
                    "Integration created and discovery is still in progress. "
                    f"Monitor it at {self._ui_url(integration.id)}.",
                    IntegrationPendingWarning,
                    stacklevel=3,
                )
            return
        if integration.status == "initializing":
            return
        if integration.status == "auth_required":
            warnings.warn(
                IntegrationAuthorizationRequired(
                    integration.id,
                    self._ui_url(integration.id),
                ),
                stacklevel=3,
            )
            return
        if integration.status == "reg_required":
            warnings.warn(
                IntegrationRegistrationRequired(
                    integration.id,
                    self._ui_url(integration.id),
                ),
                stacklevel=3,
            )
            return
        if integration.status in {
            "error",
            "disconnected",
            "disabled",
        }:
            raise IntegrationStatusError(
                integration.id or "unknown",
                integration.status,
            )

    def _ui_url(self, integration_id: str | None) -> str:
        """Return the Endeavor UI URL for an Integration."""
        if not integration_id:
            raise ValueError(
                "Integration response did not include an ID; "
                "check the MCP Servers & Tools page in Endeavor to see "
                "if the Integration is available."
            )
        return f"{self.client.prefix}://{self.client.host}/tools/{integration_id}"

    def update(
        self,
        ref: Any,
        request: IntegrationUpdate | None = None,
        **fields: Any,
    ) -> Integration:
        request = request_object(IntegrationUpdate, request, fields)
        return Integration.from_dict(
            self.client.put(request.to_dict(), "integrations", reference(ref))
        )

    def patch(
        self,
        ref: Any,
        request: IntegrationPatch | None = None,
        **fields: Any,
    ) -> Integration:
        request = request_object(IntegrationPatch, request, fields)
        return Integration.from_dict(
            self.client.patch(request.to_dict(), "integrations", reference(ref))
        )

    def delete(self, ref: Any) -> None:
        self.client.delete("integrations", reference(ref))

    def refresh(self, ref: Any) -> None:
        """Queue Integration discovery without waiting for completion."""
        self.client.get("integrations", reference(ref), "refresh")
