import pytest

from guidelight.exceptions import (
    IntegrationAuthorizationRequired,
    IntegrationPendingWarning,
    IntegrationRegistrationRequired,
    IntegrationStatusError,
    IntegrationStatusTimeout,
)
from guidelight.models import Integration
from guidelight.resources import Integrations

INTEGRATION_ID = "01ARZ3NDEKTSV4RRFFQ69G5FB3"


def test_integration_list_decodes_page_and_query(client_factory):
    client = client_factory(
        [
            {
                "page": {"page_size": 10, "offset": 0},
                "integrations": [{"id": INTEGRATION_ID, "name": "Search"}],
            }
        ]
    )

    page = Integrations(client).list(page_size=10, offset=0)

    assert page.items[0].id == INTEGRATION_ID
    assert page.items[0].catalog_included is False
    assert page.items[0].tools is None
    assert client.calls == [
        (
            "GET",
            ("integrations",),
            {"offset": 0, "page_size": 10},
        )
    ]


def test_iterate_integrations(client_factory):
    client = client_factory(
        [
            {
                "page": {"page_size": 1, "offset": 0},
                "integrations": [{"id": INTEGRATION_ID, "name": "Search"}],
            },
            {
                "page": {"page_size": 1, "offset": 1},
                "integrations": [],
            },
        ]
    )

    assert [item.id for item in Integrations(client).iterate(page_size=1)] == [
        INTEGRATION_ID
    ]
    assert client.calls[0][1] == ("integrations",)


def test_integration_get_update_patch_delete_and_refresh_routes(client_factory):
    client = client_factory(
        [
            {"id": INTEGRATION_ID, "name": "Search"},
            {"id": INTEGRATION_ID, "name": "Updated"},
            {"id": INTEGRATION_ID, "name": "Patched"},
            None,
            None,
        ]
    )
    integrations = Integrations(client)

    detail = integrations.get(INTEGRATION_ID)
    assert detail.name == "Search"
    assert detail.catalog_included is True
    assert detail.prompts == []
    assert detail.resources == []
    assert detail.tools == []
    assert integrations.update(INTEGRATION_ID, name="Updated").name == "Updated"
    assert integrations.patch(INTEGRATION_ID, name="Patched").name == "Patched"
    assert integrations.refresh(INTEGRATION_ID) is None
    integrations.delete(INTEGRATION_ID)

    assert client.calls == [
        ("GET", ("integrations", INTEGRATION_ID), None),
        ("PUT", ("integrations", INTEGRATION_ID), {"name": "Updated"}, {}),
        ("PATCH", ("integrations", INTEGRATION_ID), {"name": "Patched"}, {}),
        ("GET", ("integrations", INTEGRATION_ID, "refresh"), None),
        ("DELETE", ("integrations", INTEGRATION_ID), {}),
    ]


def test_refresh_then_wait_for_status_returns_connected_integration(
    client_factory,
    monkeypatch,
):
    client = client_factory(
        [
            None,
            {"id": INTEGRATION_ID, "status": "pending"},
            {"id": INTEGRATION_ID, "status": "connected"},
        ]
    )
    monkeypatch.setattr("guidelight.resources.integrations.time.sleep", lambda _: None)
    integrations = Integrations(client)

    integrations.refresh(INTEGRATION_ID)
    integration = integrations.wait_for_status(
        INTEGRATION_ID,
        timeout=1,
        initial_delay=0.001,
        max_delay=0.001,
    )

    assert integration.status == "connected"
    assert client.calls == [
        ("GET", ("integrations", INTEGRATION_ID, "refresh"), None),
        ("GET", ("integrations", INTEGRATION_ID), None),
        ("GET", ("integrations", INTEGRATION_ID), None),
    ]


def test_pending_creation_warns_with_monitoring_url(client_factory):
    client = client_factory(
        [{"id": INTEGRATION_ID, "name": "Search", "status": "pending"}]
    )
    client.prefix = "https"
    client.host = "endeavor.example"

    with pytest.warns(IntegrationPendingWarning, match=INTEGRATION_ID) as raised:
        integration = Integrations(client).create(
            name="Search",
            endpoint="https://mcp.example",
        )

    assert integration.id == INTEGRATION_ID
    assert integration.catalog_included is False
    assert f"https://endeavor.example/tools/{INTEGRATION_ID}" in str(raised[0].message)


@pytest.mark.parametrize(
    ("status", "warning_type"),
    [
        ("auth_required", IntegrationAuthorizationRequired),
        ("reg_required", IntegrationRegistrationRequired),
    ],
)
def test_setup_status_warns_with_integration_url(
    client_factory,
    status,
    warning_type,
):
    client = client_factory(
        [{"id": INTEGRATION_ID, "name": "Search", "status": status}]
    )
    client.prefix = "https"
    client.host = "endeavor.example"

    with pytest.warns(warning_type, match=INTEGRATION_ID):
        integration = Integrations(client).create(
            name="Search",
            endpoint="https://mcp.example",
        )

    assert integration.id == INTEGRATION_ID


def test_wait_for_status_continues_after_setup_warning(client_factory, monkeypatch):
    client = client_factory(
        [
            {"id": INTEGRATION_ID, "status": "auth_required"},
            {"id": INTEGRATION_ID, "status": "connected"},
        ]
    )
    client.prefix = "https"
    client.host = "endeavor.example"
    monkeypatch.setattr("guidelight.resources.integrations.time.sleep", lambda _: None)

    with pytest.warns(IntegrationAuthorizationRequired):
        integration = Integrations(client).wait_for_status(
            INTEGRATION_ID,
            timeout=1,
            initial_delay=0.001,
            max_delay=0.001,
        )

    assert integration.status == "connected"


@pytest.mark.parametrize("status", ["error", "disconnected", "disabled"])
def test_wait_for_status_raises_for_terminal_failure(client_factory, status):
    client = client_factory([{"id": INTEGRATION_ID, "status": status}])

    with pytest.raises(IntegrationStatusError) as raised:
        Integrations(client).wait_for_status(INTEGRATION_ID)

    assert raised.value.integration_id == INTEGRATION_ID
    assert raised.value.status == status


def test_wait_for_status_raises_after_timeout(client_factory, monkeypatch):
    client = client_factory([{"id": INTEGRATION_ID, "status": "pending"}])
    times = iter([100.0, 101.0])
    monkeypatch.setattr(
        "guidelight.resources.integrations.time.monotonic",
        lambda: next(times),
    )

    with pytest.raises(IntegrationStatusTimeout) as raised:
        Integrations(client).wait_for_status(INTEGRATION_ID, timeout=1)

    assert raised.value.integration_id == INTEGRATION_ID
    assert raised.value.status == "pending"
    assert raised.value.timeout == 1


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"timeout": 0}, "timeout must be positive"),
        ({"initial_delay": 0}, "poll delays must be positive"),
        ({"max_delay": 0}, "poll delays must be positive"),
        (
            {"initial_delay": 2, "max_delay": 1},
            "initial_delay must not exceed max_delay",
        ),
    ],
)
def test_wait_for_status_rejects_invalid_polling_options(
    client,
    options,
    message,
):
    with pytest.raises(ValueError, match=message):
        Integrations(client).wait_for_status(INTEGRATION_ID, **options)

    assert client.calls == []


@pytest.mark.parametrize("status", ["pending", "auth_required", "reg_required"])
def test_create_rejects_setup_status_without_integration_id(
    client_factory,
    status,
):
    client = client_factory([{"name": "Search", "status": status}])

    with pytest.raises(ValueError, match="did not include an ID"):
        Integrations(client).create(
            name="Search",
            endpoint="https://mcp.example",
        )


def test_integration_get_accepts_integration_model(client_factory):
    client = client_factory([{"id": INTEGRATION_ID, "name": "Search"}])

    integration = Integrations(client).get(Integration(id=INTEGRATION_ID))

    assert integration.id == INTEGRATION_ID
    assert client.calls == [
        ("GET", ("integrations", INTEGRATION_ID), None),
    ]


@pytest.mark.parametrize(
    "operation",
    [
        lambda integrations: integrations.get("not-a-ulid"),
        lambda integrations: integrations.update("not-a-ulid", name="Updated"),
        lambda integrations: integrations.patch("not-a-ulid", name="Patched"),
        lambda integrations: integrations.delete("not-a-ulid"),
        lambda integrations: integrations.refresh("not-a-ulid"),
        lambda integrations: integrations.wait_for_status("not-a-ulid"),
    ],
)
def test_integration_routes_reject_invalid_references_before_request(
    client,
    operation,
):
    integrations = Integrations(client)

    with pytest.raises(ValueError, match="valid ULID"):
        operation(integrations)

    assert client.calls == []
