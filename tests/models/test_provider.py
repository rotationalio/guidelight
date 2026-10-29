"""Tests for provider and provider-credential models."""

import pytest
from pydantic import ValidationError

from guidelight.models import (
    Provider,
    ProviderCreate,
    ProviderCredential,
    ProviderCredentialCreate,
    ProviderCredentialPatch,
    ProviderCredentialUpdate,
    ProviderPatch,
    ProviderUpdate,
)


def test_provider_create_serializes_writable_fields():
    """Provider creation emits the configured provider values."""
    request = ProviderCreate(
        name="OpenRouter",
        endpoint="https://openrouter.ai/api",
        catalog_url="https://openrouter.ai/models",
        credential=ProviderCredentialCreate(credentials={"api_key": "secret"}),
        slug="openrouter",
    )

    assert request.to_dict()["name"] == "OpenRouter"
    assert request.to_dict()["endpoint"].startswith("https://")
    assert request.to_dict()["slug"] == "openrouter"
    assert request.to_dict()["credential"]["credentials"] == {"api_key": "secret"}


def test_provider_request_rejects_response_only_fields():
    """Provider status and catalog timestamps cannot be sent in requests."""
    with pytest.raises(ValidationError):
        ProviderCreate(
            name="OpenRouter",
            endpoint="https://openrouter.ai/api",
            catalog_url="https://openrouter.ai/models",
            credential=ProviderCredentialCreate(credentials={"api_key": "secret"}),
            status="ready",
        )


def test_provider_create_requires_an_initial_credential():
    """Provider creation cannot omit its initial credential."""
    with pytest.raises(ValidationError):
        ProviderCreate(
            name="OpenRouter",
            endpoint="https://openrouter.ai/api",
            catalog_url="https://openrouter.ai/models",
        )


def test_provider_response_preserves_unknown_server_fields():
    """Provider responses retain future fields through the extra mapping."""
    provider = Provider.model_validate(
        {
            "id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "name": "OpenRouter",
            "extra": {"region": "us"},
            "future_field": "preserved",
        }
    )

    assert provider.provider_extra == {"region": "us"}
    assert provider.extra["future_field"] == "preserved"
    assert "extra" not in provider.extra


def test_provider_update_and_patch_match_writable_server_fields():
    """Provider PUT and PATCH requests include supported mutable fields."""
    update = ProviderUpdate(
        name="OpenRouter",
        slug="openrouter",
        endpoint="https://openrouter.ai/api",
        catalog_url="https://openrouter.ai/models",
    )
    patch = ProviderPatch(slug="openrouter-updated")

    assert update.to_dict()["slug"] == "openrouter"
    assert patch.to_dict() == {"slug": "openrouter-updated"}


@pytest.mark.parametrize(
    "fields",
    [
        {},
        {"name": ""},
        {"endpoint": " "},
        {"catalog_url": ""},
        {"is_default": False},
    ],
)
def test_provider_patch_rejects_invalid_server_bodies(fields):
    """Provider PATCH validation fails before invalid bodies are sent."""
    with pytest.raises(ValidationError):
        ProviderPatch(**fields)


def test_credential_request_rejects_response_only_fields():
    """Credential metadata fields cannot be added to a create request."""
    with pytest.raises(ValidationError):
        ProviderCredentialCreate(
            credentials={"api_key": "secret"},
            status="connected",
        )


def test_credential_response_does_not_define_secret_fields():
    """Credential responses expose metadata, not a credentials payload field."""
    credential = ProviderCredential.model_validate(
        {
            "provider_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "name": "Default",
        }
    )

    assert not hasattr(credential, "credentials")


def test_credential_update_can_set_default_without_a_name():
    """Credential PUT accepts the server-supported default-only body."""
    request = ProviderCredentialUpdate(is_default=True)

    assert request.to_dict() == {"is_default": True}


@pytest.mark.parametrize(
    "request_type, fields",
    [
        (ProviderCredentialUpdate, {}),
        (ProviderCredentialPatch, {}),
        (ProviderCredentialPatch, {"name": ""}),
        (ProviderCredentialPatch, {"is_default": False}),
    ],
)
def test_credential_updates_reject_invalid_server_bodies(
    request_type,
    fields,
):
    """Credential PUT and PATCH models enforce Endeavor validation."""
    with pytest.raises(ValidationError):
        request_type(**fields)
