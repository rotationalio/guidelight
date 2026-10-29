"""Route tests for provider-scoped credential managers."""

import pytest

from guidelight.models import (
    ProviderCredentialCreate,
    ProviderCredentialPatch,
    ProviderCredentialUpdate,
)
from guidelight.resources import ProviderCredentials

from .shared import PROVIDER_ID, SECRET_ID


def test_credentials_remain_provider_scoped(client_factory):
    """Credential CRUD paths include the parent provider reference."""
    client = client_factory(
        [
            {"page": {}, "credentials": []},
            {"secret_id": SECRET_ID, "name": "Default"},
        ]
    )
    credentials = ProviderCredentials(client, "openrouter")

    credentials.list()
    created = credentials.create(
        ProviderCredentialCreate(credentials={"api_key": "test"})
    )

    assert created.secret_id == SECRET_ID
    assert client.calls[0][1] == (
        "providers",
        "openrouter",
        "credentials",
    )
    assert client.calls[1][1] == (
        "providers",
        "openrouter",
        "credentials",
    )


def test_credential_metadata_and_actions_remain_provider_scoped(
    client_factory,
):
    """Credential metadata actions and connectivity retain the parent provider."""
    client = client_factory(
        [
            {"secret_id": SECRET_ID, "name": "Default"},
            {"secret_id": SECRET_ID, "name": "Renamed"},
            {"secret_id": SECRET_ID, "name": "Renamed", "is_default": True},
            {"success": True, "status": "connected"},
        ]
    )
    credentials = ProviderCredentials(client, PROVIDER_ID)

    default = credentials.default()
    updated = credentials.update(
        SECRET_ID,
        ProviderCredentialUpdate(name="Renamed"),
    )
    patched = credentials.patch(
        SECRET_ID,
        ProviderCredentialPatch(is_default=True),
    )
    status = credentials.test_connectivity(SECRET_ID)
    credentials.delete(SECRET_ID)

    assert default.secret_id == SECRET_ID
    assert updated.name == "Renamed"
    assert patched.is_default is True
    assert status.success is True
    collection_path = ("providers", PROVIDER_ID, "credentials")
    assert [call[0:2] for call in client.calls] == [
        ("GET", (*collection_path, "default")),
        ("PUT", (*collection_path, SECRET_ID)),
        ("PATCH", (*collection_path, SECRET_ID)),
        ("GET", (*collection_path, SECRET_ID, "test-connectivity")),
        ("DELETE", (*collection_path, SECRET_ID)),
    ]


@pytest.mark.parametrize(
    "operation",
    [
        lambda manager: manager.create(credentials={}),
        lambda manager: manager.update(SECRET_ID),
        lambda manager: manager.patch(SECRET_ID, is_default=False),
    ],
)
def test_invalid_credential_bodies_fail_before_request(
    client_factory,
    operation,
):
    """Invalid credential requests fail before reaching the client."""
    client = client_factory()

    with pytest.raises(TypeError, match="invalid ProviderCredential"):
        operation(ProviderCredentials(client, PROVIDER_ID))

    assert client.calls == []
