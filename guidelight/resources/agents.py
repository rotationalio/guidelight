"""Agent resource managers."""

from __future__ import annotations

from typing import Any

from ..models.agent import Agent, AgentCreate, AgentUpdate
from .base import Page, ResourceManager, decode_page, reference


class AgentTasks(ResourceManager):
    """Boundary for the agent-scoped task endpoints.

    Task response models and operations are introduced in a later SDK phase.
    """

    def __init__(self, client, agent_reference: str):
        """  
        agent_reference: str - normalized identifier for an Agent.
        Can be a slug or an ID.
        """
        super().__init__(client)
        self.agent_reference = agent_reference

    @property
    def collection_path(self) -> tuple[str, ...]:
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
        query = self._query(
            page_size=page_size,
            offset=offset,
            order_by=order_by,
            filters=filters,
        )
        body = self.client.get(*self.collection_path, query=query)
        return decode_page(body, key="agents", model=Agent)

    def get(self, ref: Any) -> Agent:
        body = self.client.get(
            *self._path(reference(ref, allow_slug=True)),
        )
        return Agent.from_dict(body)

    def create(
        self,
        request: AgentCreate | None = None,
        **fields: Any,
    ) -> Agent:
        request = self._request(AgentCreate, request, fields)
        body = self.client.post(request.to_dict(), *self.collection_path)
        return Agent.from_dict(body)

    def update(
        self,
        ref: Any,
        request: AgentUpdate | None = None,
        **fields: Any,
    ) -> Agent:
        request = self._request(AgentUpdate, request, fields)
        body = self.client.put(
            request.to_dict(),
            *self._path(reference(ref, allow_slug=True)),
        )
        return Agent.from_dict(body)

    def delete(self, ref: Any) -> None:
        self.client.delete(*self._path(reference(ref, allow_slug=True)))

    def tasks(self, ref: Any) -> AgentTasks:
        return AgentTasks(
            self.client,
            reference(ref, allow_slug=True),
        )

    @staticmethod
    def _request(request_type, request, fields):
        if request is not None and fields:
            raise TypeError("provide either a request object or keyword fields")
        if request is not None and not isinstance(request, request_type):
            raise TypeError(f"expected {request_type.__name__}")
        if request is None:
            try:
                request = request_type(**fields)
            except TypeError as exc:
                raise TypeError(f"invalid {request_type.__name__} fields") from exc
        return request
