from __future__ import annotations

from ..models import (
    Generation,
    GenerationFeedback,
    GenerationFeedbackResponse,
    GenerationTestCaseCreate,
    GoldenExamples,
    Metric,
    TestCase,
)
from .base import (
    Page,
    ResourceManager,
    decode_page,
    reference,
    request_object,
)
from .comments import Comments


class Generations(ResourceManager):
    """Manager for the Generation resource."""

    collection_path = ("generations",)
    valid_filters = frozenset({"experiment_id", "release_id"})

    def list(
        self, *, experiment_id=None, release_id=None, **options
    ) -> Page[Generation]:
        """List Generations filtered by Experiment or Release."""
        if experiment_id is not None and release_id is not None:
            raise ValueError("experiment_id and release_id are mutually exclusive")
        filters = {
            key: value
            for key, value in {
                "experiment_id": experiment_id,
                "release_id": release_id,
            }.items()
            if value is not None
        }
        query = self._query(filters=filters, **options)
        body = self.client.get(*self.collection_path, query=query)
        return decode_page(body, key="generations", model=Generation)

    def get(self, ref) -> Generation:
        """Retrieve a Generation by ID or supported reference."""
        return Generation.from_dict(self.client.get("generations", reference(ref)))

    def delete(self, ref) -> None:
        """Delete a Generation by ID or supported reference."""
        self.client.delete("generations", reference(ref))

    def metrics(self, ref) -> Page[Metric]:
        """Retrieve metric results associated with a Generation."""
        body = self.client.get("generations", reference(ref), "metrics")
        return decode_page(body, key="metrics", model=Metric)

    def feedback(self, ref, request=None, **fields):
        """Submit feedback scores for a Generation."""
        request = request_object(GenerationFeedback, request, fields)
        body = self.client.post(
            request.to_dict(), "generations", reference(ref), "feedback"
        )
        return GenerationFeedbackResponse.from_dict(body)

    def set_golden(self, ref, test_case_ids: list[str]):
        """Set the Test Cases used as golden examples for a Generation."""
        return self.client.post(
            GoldenExamples(test_case_ids=test_case_ids).to_dict(),
            "generations",
            reference(ref),
            "golden",
        )

    def create_test_case(self, ref, request=None, **fields) -> TestCase:
        """Save a Generation as a new Test Case associated with Tasks."""
        request = request_object(GenerationTestCaseCreate, request, fields)
        body = self.client.post(
            request.to_dict(),
            "generations",
            reference(ref),
            "testcase",
        )
        return TestCase.from_dict(body)

    def comments(self, ref) -> Comments:
        """Return a Comment manager scoped to a Generation."""
        return Comments(self.client, "generations", reference(ref))
