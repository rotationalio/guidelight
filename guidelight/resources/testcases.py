from __future__ import annotations
from typing import Any

from ..models import TestCase, TestCaseCreate, TestCaseUpdate, TestCaseVersion
from .base import (
    Page,
    ResourceManager,
    decode_page,
    request_object,
    resolve_resource_ref,
    reference,
)


class TestCases(ResourceManager):
    """Manager for the Test Case resource."""

    collection_path = ("testcases",)
    valid_filters = frozenset(
        {
            "agent_id",
            "task_id",
            "experiment_id",
            "context_type",
            "input_modality",
        }
    )

    def __init__(self, client, *, agent=None, task=None, experiment=None):
        """Create a Test Case manager with at most one parent scope."""
        super().__init__(client)
        values = [agent, task, experiment]
        if sum(value is not None for value in values) > 1:
            raise ValueError("only one Test Case parent may be selected")
        if agent is not None:
            self.parent = ("agents", resolve_resource_ref(agent))
        elif task is not None:
            self.parent = ("tasks", resolve_resource_ref(task))
        elif experiment is not None:
            self.parent = ("experiments", resolve_resource_ref(experiment))
        else:
            self.parent = None

    def list(self, **options) -> Page[TestCase]:
        """List Test Cases using supported filters and pagination options."""
        filters = {
            key: options.pop(key) for key in list(options) if key in self.valid_filters
        }
        query = self._query(filters=filters, **options)
        path = self.parent + ("testcases",) if self.parent else self.collection_path
        body = self.client.get(*path, query=query)
        return decode_page(body, key="testcases", model=TestCase)

    def get(self, ref: Any) -> TestCase:
        """Retrieve a Test Case by ID or supported reference."""
        return TestCase.from_dict(self.client.get("testcases", reference(ref)))

    def create(self, request=None, **fields) -> TestCase:
        """Create a Test Case in the configured collection."""
        request = request_object(TestCaseCreate, request, fields)
        return TestCase.from_dict(
            self.client.post(request.to_dict(), *self.collection_path)
        )

    def update(self, ref, request=None, **fields) -> TestCase:
        """Update a Test Case by ID or supported reference."""
        request = request_object(TestCaseUpdate, request, fields)
        return TestCase.from_dict(
            self.client.put(request.to_dict(), "testcases", reference(ref))
        )

    def delete(self, ref) -> None:
        """Delete a Test Case by ID or supported reference."""
        self.client.delete("testcases", reference(ref))

    def set_golden(self, ref, generation_id: str) -> TestCase:
        """Set the Generation used as the Test Case golden example."""
        test_case_ref = reference(ref)
        body = self.client.put(
            {"generation_id": generation_id},
            "testcases",
            test_case_ref,
            "golden",
        )
        if body is None:
            return self.get(test_case_ref)
        return TestCase.from_dict(body)

    def versions(self, ref) -> TestCaseVersions:
        """Return a version manager scoped to a Test Case."""
        return TestCaseVersions(self.client, ref)


class TestCaseVersions(ResourceManager):
    """Manager for versions belonging to one Test Case."""

    def __init__(self, client, test_case: str):
        """Create a Test Case version manager."""
        super().__init__(client)
        self.test_case = reference(test_case)

    def get(self, version: int) -> TestCaseVersion:
        """Retrieve a specific Test Case version."""
        body = self.client.get("testcases", self.test_case, "versions", str(version))
        return TestCaseVersion.from_dict(body)

    def delete(self, version: int) -> None:
        """Delete a specific Test Case version."""
        self.client.delete("testcases", self.test_case, "versions", str(version))
