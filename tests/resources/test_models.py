"""Route tests for the read-only model catalog manager."""

import pytest

from guidelight.resources import Models

from .shared import MODEL_ID


def test_model_catalog_list_forwards_supported_filters(client_factory):
    """Model catalog filters are forwarded without adding write operations."""
    client = client_factory([{"page": {}, "models": [{"id": MODEL_ID}]}])

    page = Models(client).list(provider_id="provider-1", is_moderated=True)

    assert page.items[0].id == MODEL_ID
    assert client.calls[0][1] == ("models",)
    assert client.calls[0][2]["provider_id"] == "provider-1"
    assert client.calls[0][2]["is_moderated"] is True


@pytest.mark.parametrize(
    ("filter_name", "value"),
    [
        ("restricted", True),
        ("provider_id", "provider-1"),
        ("author", "OpenAI"),
        ("published_after", "2025-01-01"),
        ("published_before", "2026-01-01"),
        ("input_modality", "text"),
        ("output_modality", "text"),
        ("context_size_above", 8192),
        ("capabilities", ["tools"]),
        ("input_cost_limit", 1.0),
        ("output_cost_limit", 2.0),
        ("tpm_limit", 1000),
        ("rpm_limit", 60),
        ("is_moderated", True),
        ("api_type", "openai"),
        ("auth_type", "api-key"),
        ("selected_model_id", MODEL_ID),
    ],
)
def test_model_catalog_forwards_every_supported_filter(
    client_factory,
    filter_name,
    value,
):
    """Every advertised model-catalog filter reaches the request query."""
    client = client_factory([{"page": {}, "models": []}])

    Models(client).list(**{filter_name: value})

    assert client.calls[0][2][filter_name] == value


def test_model_usage_is_typed(client_factory):
    """Model usage responses decode into their dedicated response type."""
    client = client_factory([{"agent_count": 3, "deployed_count": 1}])
    models = Models(client)

    usage = models.usage(MODEL_ID)

    assert usage.agent_count == 3


def test_provider_scoped_catalog_uses_global_model_detail_routes(client_factory):
    """Provider scope applies only to catalog listing."""
    client = client_factory(
        [
            {"page": {}, "models": []},
            {"id": MODEL_ID, "name": "Example"},
            {"agent_count": 1},
        ]
    )
    models = Models(client, provider="openrouter")

    models.list()
    models.get(MODEL_ID)
    models.usage(MODEL_ID)

    assert [call[1] for call in client.calls] == [
        ("providers", "openrouter", "models"),
        ("models", MODEL_ID),
        ("models", MODEL_ID, "usage"),
    ]
