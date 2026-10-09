"""Agent resource managers."""

from __future__ import annotations

from typing import Any

from ..models.agent import Agent, AgentCreate, AgentUpdate
from .base import Page, ResourceManager, decode_page, reference, request_object
from .tasks import Tasks


class AgentTasks(Tasks):
    """Task manager scoped to one Agent."""

    def __init__(self, client, agent_reference: str):
        """Create a Task manager scoped to an Agent."""
        super().__init__(client, agent_reference)
        self.agent_reference = self.agent

    @property
    def collection_path(self) -> tuple[str, ...]:
        """Return the Agent-scoped Task collection path."""
        return ("agents", self.agent_reference, "tasks")


class Agents(ResourceManager):
    """High-level manager for the Agent resource."""

    collection_path = ("agents",)
    valid_filters = frozenset()

    def list(
        self,
        *,
        page_size: int | None = None,
        offset: int = 0,
        order_by: str | list[str] | None = None,
        **filters: Any,
    ) -> Page[Agent]:
        """List Agents using supported filters and pagination options."""
        query = self._query(
            page_size=page_size,
            offset=offset,
            order_by=order_by,
            filters=filters,
        )
        body = self.client.get(*self.collection_path, query=query)
        return decode_page(body, key="agents", model=Agent)

    def get(self, ref: Any) -> Agent:
        """Retrieve an Agent by ID or supported slug."""
        body = self.client.get(
            *self._path(reference(ref, allow_slug=True)),
        )
        return Agent.from_dict(body)

    def create(
        self,
        request: AgentCreate | None = None,
        **fields: Any,
    ) -> Agent:
        """Create an Agent from a request model or keyword fields."""
        request = request_object(AgentCreate, request, fields)
        body = self.client.post(request.to_dict(), *self.collection_path)
        return Agent.from_dict(body)

    def update(
        self,
        ref: Any,
        request: AgentUpdate | None = None,
        **fields: Any,
    ) -> Agent:
        """Update an Agent by ID or supported slug."""
        request = request_object(AgentUpdate, request, fields)
        body = self.client.put(
            request.to_dict(),
            *self._path(reference(ref, allow_slug=True)),
        )
        return Agent.from_dict(body)

    def delete(self, ref: Any) -> None:
        """Delete an Agent by ID or supported slug."""
        self.client.delete(*self._path(reference(ref, allow_slug=True)))

    def tasks(self, ref: Any) -> AgentTasks:
        """Return a Task boundary scoped to an Agent."""
        return AgentTasks(
            self.client,
            reference(ref, allow_slug=True),
        )
