import pytest
from pydantic import SecretStr, ValidationError

from guidelight.models import (
    Integration,
    IntegrationCreate,
    IntegrationPatch,
    IntegrationUpdate,
    OAuthCredentials,
)


def test_integration_preserves_catalog_omission():
    integration = Integration.model_validate(
        {
            "id": "integration-1",
            "prompts": None,
            "resources": None,
            "tools": None,
        }
    )

    assert integration.prompts is None
    assert integration.resources is None
    assert integration.tools is None
    assert integration.catalog_included is False


def test_integration_reports_when_catalog_is_included():
    integration = Integration.model_validate(
        {
            "id": "integration-1",
            "prompts": [],
            "resources": [],
            "tools": [],
        }
    )

    assert integration.catalog_included is True


def test_integration_accepts_camel_case_server_fields():
    integration = Integration.model_validate(
        {
            "protocolVersion": "2025-03-26",
            "serverInfo": {"name": "Notion"},
            "lastRefresh": "2026-11-12T12:00:00Z",
            "oauthConfigured": True,
        }
    )

    assert integration.protocol_version == "2025-03-26"
    assert integration.server_info == {"name": "Notion"}
    assert integration.last_refresh is not None
    assert integration.oauth_configured is True
    assert integration.extra == {}


@pytest.mark.parametrize("request_type", [IntegrationCreate, IntegrationUpdate])
def test_integration_requests_reject_blank_names(request_type):
    with pytest.raises(ValidationError):
        request_type(name=" ", endpoint="https://mcp.example")


@pytest.mark.parametrize(
    "request_type",
    [IntegrationCreate, IntegrationUpdate, IntegrationPatch],
)
@pytest.mark.parametrize(
    "endpoint",
    [
        "not-a-url",
        "ftp://mcp.example/server",
        "https:///missing-host",
        "https://mcp.example:not-a-port/server",
        "https://bad host/server",
    ],
)
def test_integration_requests_reject_invalid_endpoints(request_type, endpoint):
    with pytest.raises(
        ValidationError,
        match="endpoint must be a valid HTTP or HTTPS URL",
    ):
        request_type(name="Search", endpoint=endpoint)


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://mcp.example/server",
        "http://localhost:8080/mcp",
        "https://mcp.example/server?version=1",
    ],
)
def test_integration_create_preserves_valid_http_endpoints(endpoint):
    request = IntegrationCreate(name="Search", endpoint=endpoint)

    assert request.endpoint == endpoint
    assert request.to_dict()["endpoint"] == endpoint


def test_integration_patch_serializes_only_supplied_fields():
    request = IntegrationPatch(name="Updated Search")

    assert request.to_dict() == {"name": "Updated Search"}


def test_oauth_credentials_mask_secret_but_serialize_it_for_requests():
    request = OAuthCredentials(
        client_id="client-id",
        client_secret="client-secret",
    )

    assert isinstance(request.client_secret, SecretStr)
    assert str(request.client_secret) == "**********"
    assert request.client_secret.get_secret_value() == "client-secret"
    assert request.to_dict() == {
        "clientId": "client-id",
        "clientSecret": "client-secret",
    }


def test_integration_create_serializes_nested_oauth_credentials_for_endeavor():
    request = IntegrationCreate(
        name="Search",
        endpoint="https://mcp.example",
        credentials={
            "clientId": "client-id",
            "clientSecret": "client-secret",
        },
    )

    assert request.to_dict() == {
        "name": "Search",
        "endpoint": "https://mcp.example",
        "credentials": {
            "clientId": "client-id",
            "clientSecret": "client-secret",
        },
    }


def test_empty_oauth_credentials_request_dynamic_client_registration():
    assert OAuthCredentials().to_dict() == {}


def test_oauth_credentials_reject_secret_without_client_id():
    with pytest.raises(ValidationError, match="client_id is required"):
        OAuthCredentials(client_secret="client-secret")
