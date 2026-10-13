from __future__ import annotations

from typing import Any

from ..models import Task, TaskCreate, TaskUpdate
from .base import (
    Page,
    ResourceManager,
    decode_page,
    request_object,
    resolve_resource_ref,
)
from .experiments import Experiments
from .metrics import Metrics
from .releases import Releases
from .testcases import TestCases


class Tasks(ResourceManager):
    """Tasks scoped to one Agent."""

    def __init__(self, client, agent: Any):
        """Create a task manager scoped to an Agent."""
        super().__init__(client)
        self.agent = resolve_resource_ref(agent)

    @property
    def collection_path(self):
        """Return the Agent-scoped Task collection path."""
        return ("agents", self.agent, "tasks")

    def list(self, **options) -> Page[Task]:
        """List Tasks belonging to the configured Agent."""
        query = self._query(**options)
        body = self.client.get(*self.collection_path, query=query)
        return decode_page(body, key="tasks", model=Task)

    def get(self, ref: Any) -> Task:
        """Retrieve a Task by ID or supported reference."""
        return Task.from_dict(self.client.get("tasks", resolve_resource_ref(ref)))

    def create(self, request: TaskCreate | None = None, **fields: Any) -> Task:
        """Create a Task under the configured Agent."""
        request = request_object(TaskCreate, request, fields)
        body = self.client.post(request.to_dict(), *self.collection_path)
        return Task.from_dict(body)

    def update(self, ref: Any, request: TaskUpdate | None = None, **fields) -> Task:
        """Update a Task by ID or supported reference."""
        request = request_object(TaskUpdate, request, fields)
        body = self.client.put(request.to_dict(), "tasks", resolve_resource_ref(ref))
        return Task.from_dict(body)

    def delete(self, ref: Any) -> None:
        """Delete a Task by ID or supported reference."""
        self.client.delete("tasks", resolve_resource_ref(ref))

    def experiments(self, ref: Any) -> Experiments:
        """Return an Experiment manager scoped to a Task."""
        return Experiments(self.client, task=resolve_resource_ref(ref))

    def test_cases(self, ref: Any) -> TestCases:
        """Return a Test Case manager scoped to a Task."""
        return TestCases(self.client, task=resolve_resource_ref(ref))

    def metrics(self, ref: Any) -> Metrics:
        """Return a Metric manager scoped to a Task."""
        return Metrics(self.client, task=resolve_resource_ref(ref))

    def releases(self, ref: Any) -> Releases:
        """Return a Release manager scoped to a Task."""
        return Releases(self.client, task=resolve_resource_ref(ref))
