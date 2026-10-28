"""Route and action tests for provider managers."""

from guidelight.models import (
    ProviderCreate,
    ProviderCredentialCreate,
    ProviderPatch,
    ProviderUpdate,
)
from guidelight.resources import Providers

from .shared import PROVIDER_ID


def test_provider_default_and_connectivity_routes(client_factory):
    """Provider actions use their explicit action endpoints."""
    client = client_factory(
        [
            {"id": PROVIDER_ID, "name": "Default"},
            {"success": True, "status": "connected"},
        ]
    )
    providers = Providers(client)

    providers.default()
    status = providers.test_connectivity("openrouter")

    assert status.status == "connected"
    assert client.calls == [
        ("GET", ("providers", "default"), None),
        (
            "GET",
            ("providers", "openrouter", "test-connectivity"),
            None,
        ),
    ]


def test_provider_create_requires_and_sends_initial_credential(client_factory):
    """Provider creation sends Endeavor's complete create form."""
    client = client_factory(
        [{"id": PROVIDER_ID, "name": "OpenRouter", "slug": "openrouter"}]
    )
    providers = Providers(client)

    provider = providers.create(
        ProviderCreate(
            name="OpenRouter",
            slug="openrouter",
            endpoint="https://openrouter.ai/api",
            catalog_url="https://openrouter.ai/models",
            credential=ProviderCredentialCreate(credentials={"api_key": "secret"}),
        )
    )

    assert provider.id == PROVIDER_ID
    assert client.calls[0][0:2] == ("POST", ("providers",))
    assert client.calls[0][2]["credential"]["credentials"] == {"api_key": "secret"}


def test_provider_get_update_patch_and_delete_accept_slugs(client_factory):
    """Provider detail operations preserve ULID-or-slug references."""
    client = client_factory(
        [
            {"id": PROVIDER_ID, "name": "OpenRouter", "slug": "openrouter"},
            {"id": PROVIDER_ID, "name": "OpenRouter", "slug": "openrouter"},
            {
                "id": PROVIDER_ID,
                "name": "OpenRouter",
                "description": "Updated",
            },
        ]
    )
    providers = Providers(client)

    retrieved = providers.get("openrouter")
    updated = providers.update(
        "openrouter",
        ProviderUpdate(
            name="OpenRouter",
            endpoint="https://openrouter.ai/api",
            catalog_url="https://openrouter.ai/models",
        ),
    )
    patched = providers.patch(
        "openrouter",
        ProviderPatch(description="Updated"),
    )
    providers.delete("openrouter")

    assert retrieved.id == PROVIDER_ID
    assert updated.name == "OpenRouter"
    assert patched.description == "Updated"
    assert [call[0:2] for call in client.calls] == [
        ("GET", ("providers", "openrouter")),
        ("PUT", ("providers", "openrouter")),
        ("PATCH", ("providers", "openrouter")),
        ("DELETE", ("providers", "openrouter")),
    ]


def test_provider_no_content_actions_accept_slugs(client_factory):
    """Provider refresh and status updates do not decode empty responses."""
    client = client_factory([None, None])
    providers = Providers(client)

    assert providers.refresh_catalog("openrouter") is None
    assert providers.update_status("openrouter", "pending") is None

    assert client.calls == [
        (
            "POST",
            ("providers", "openrouter", "refresh-catalog"),
            {},
            {},
        ),
        (
            "PATCH",
            ("providers", "openrouter", "status", "pending"),
            {},
            {},
        ),
    ]


def test_provider_scoped_managers_preserve_provider_reference(client_factory):
    """Provider child managers retain the provider in their route scope."""
    client = client_factory(
        [
            {"page": {}, "models": []},
            {"page": {}, "credentials": []},
            {"page": {}, "policies": [], "provider_id": PROVIDER_ID},
        ]
    )
    providers = Providers(client)

    providers.models("openrouter").list()
    providers.credentials("openrouter").list()
    policies = providers.governance("openrouter").list()

    assert policies.metadata["provider_id"] == PROVIDER_ID
    assert [call[1] for call in client.calls] == [
        ("providers", "openrouter", "models"),
        ("providers", "openrouter", "credentials"),
        ("providers", "openrouter", "models", "governance"),
    ]
