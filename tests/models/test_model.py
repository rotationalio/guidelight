"""Tests for the read-only model catalog types."""

from guidelight.models import Model, ModelUsage


def test_catalog_model_decodes_and_preserves_unknown_fields():
    """Catalog model responses retain server additions."""
    model = Model.model_validate(
        {
            "id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "name": "Example Model",
            "context_size": 128000,
            "future_field": {"supported": True},
        }
    )

    assert model.context_size == 128000
    assert model.extra["future_field"]["supported"] is True


def test_model_usage_decodes_envelope():
    """Usage and deployment summary responses decode as typed models."""
    usage = ModelUsage.model_validate({"agent_count": 2, "deployed_count": 1})

    assert usage.agent_count == 2
