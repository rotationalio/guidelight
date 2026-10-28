"""Route and response tests for environment managers."""

import pytest

from guidelight.models import EnvironmentCreate, EnvironmentUpdate
from guidelight.resources import Environments

from .shared import PROVIDER_ID


def test_environment_list_forwards_provider_filter(client_factory):
    """Environment listing uses the documented envelope and filter."""
    client = client_factory(
        [{"page": {"page_size": 10, "offset": 0}, "environments": []}]
    )

    page = Environments(client).list(provider_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")

    assert page.items == []
    assert client.calls[0] == (
        "GET",
        ("environments",),
        {
            "offset": 0,
            "provider_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        },
    )


def test_environment_create_uses_global_route(client_factory):
    """Environment creation posts to the global collection."""
    client = client_factory(
        [{"id": "01ARZ3NDEKTSV4RRFFQ69G5FAV", "name": "Production"}]
    )

    environment = Environments(client).create(
        EnvironmentCreate(name="Production", slug="production")
    )

    assert environment.name == "Production"
    assert client.calls[0][0:2] == ("POST", ("environments",))


def test_environment_get_update_patch_and_delete_use_global_routes(client_factory):
    """Environment detail operations use the environment ULID route."""
    client = client_factory(
        [
            {"id": PROVIDER_ID, "name": "Production", "slug": "production"},
            {"id": PROVIDER_ID, "name": "Staging", "slug": "staging"},
            {"id": PROVIDER_ID, "name": "Staging", "description": "Updated"},
        ]
    )
    environments = Environments(client)

    retrieved = environments.get(PROVIDER_ID)
    updated = environments.update(
        PROVIDER_ID,
        EnvironmentUpdate(name="Staging", slug="staging"),
    )
    patched = environments.patch(PROVIDER_ID, description="Updated")
    environments.delete(PROVIDER_ID)

    assert retrieved.name == "Production"
    assert updated.slug == "staging"
    assert patched.description == "Updated"
    assert [call[0:2] for call in client.calls] == [
        ("GET", ("environments", PROVIDER_ID)),
        ("PUT", ("environments", PROVIDER_ID)),
        ("PATCH", ("environments", PROVIDER_ID)),
        ("DELETE", ("environments", PROVIDER_ID)),
    ]


@pytest.mark.parametrize(
    "operation",
    [
        lambda manager: manager.create(name="", slug="production"),
        lambda manager: manager.update(PROVIDER_ID, name="Production", slug=""),
    ],
)
def test_invalid_environment_create_and_update_fail_before_request(
    client_factory,
    operation,
):
    """Invalid Environment POST and PUT bodies never reach the client."""
    client = client_factory()

    with pytest.raises(TypeError, match="invalid Environment"):
        operation(Environments(client))

    assert client.calls == []


@pytest.mark.parametrize(
    "fields",
    [
        {"name": ""},
        {"slug": " "},
        {"provider": {}},
        {"is_default": False},
    ],
)
def test_invalid_environment_patch_fails_before_request(
    client_factory,
    fields,
):
    """Invalid Environment PATCH fields never reach the client."""
    client = client_factory()

    with pytest.raises(TypeError, match="invalid EnvironmentPatch fields"):
        Environments(client).patch(
            "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            **fields,
        )

    assert client.calls == []
