"""Request models for updating many-to-many resource associations."""

from .base import RequestModel


class AssociationUpdate(RequestModel):
    """Test Case version identifiers submitted for an association update."""

    ids: list[str]

    def to_dict(self) -> dict[str, list[str]]:
        """Serialize identifiers using the API's association field name."""
        return {"test_case_version_ids": list(self.ids)}


class GoldenExamples(RequestModel):
    """Test Case identifiers submitted as golden examples."""

    test_case_ids: list[str]

    def to_dict(self) -> dict[str, list[str]]:
        """Serialize identifiers using the API's golden-example field name."""
        return {"test_case_ids": list(self.test_case_ids)}
