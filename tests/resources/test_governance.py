"""Route and scope tests for governance policy managers."""

import pytest

from guidelight.models import GovernancePolicyCreate, GovernancePolicyPatch
from guidelight.resources import GovernancePolicies

from .shared import POLICY_ID, PROVIDER_ID


def test_global_governance_forwards_active_filter(client_factory):
    """Global governance listing preserves the active filter."""
    client = client_factory([{"page": {}, "policies": []}])

    GovernancePolicies(client).list(active=True)

    assert client.calls[0] == (
        "GET",
        ("models", "governance"),
        {"offset": 0, "active": True},
    )


def test_global_governance_crud_uses_model_governance_routes(client_factory):
    """Global policy CRUD uses the model-governance collection."""
    client = client_factory(
        [
            {"id": POLICY_ID, "name": "Default", "policy_type": "model"},
            {"id": POLICY_ID, "name": "Default", "policy_type": "model"},
            {"id": POLICY_ID, "name": "Updated", "policy_type": "model"},
        ]
    )
    policies = GovernancePolicies(client)

    created = policies.create(
        GovernancePolicyCreate(
            name="Default",
            policy_type="model",
            constraints={"allowed": True},
        )
    )
    retrieved = policies.get(POLICY_ID)
    patched = policies.patch(
        POLICY_ID,
        GovernancePolicyPatch(name="Updated"),
    )
    policies.delete(POLICY_ID)

    assert created.id == POLICY_ID
    assert retrieved.name == "Default"
    assert patched.name == "Updated"
    collection_path = ("models", "governance")
    assert [call[0:2] for call in client.calls] == [
        ("POST", collection_path),
        ("GET", (*collection_path, POLICY_ID)),
        ("PATCH", (*collection_path, POLICY_ID)),
        ("DELETE", (*collection_path, POLICY_ID)),
    ]


def test_global_governance_preserves_response_metadata(client_factory):
    """Global policy list metadata remains available on the decoded page."""
    client = client_factory(
        [
            {
                "page": {},
                "policies": [],
                "scope": "global",
            }
        ]
    )

    page = GovernancePolicies(client).list()

    assert page.metadata == {"scope": "global"}


def test_provider_governance_preserves_parent_scope(client_factory):
    """Provider governance uses its read-only provider collection route."""
    client = client_factory(
        [
            {
                "page": {},
                "policies": [{"id": POLICY_ID, "name": "Default", "active": True}],
                "provider_id": PROVIDER_ID,
            }
        ]
    )
    policies = GovernancePolicies(client, provider="openrouter")

    page = policies.list()

    assert page.items[0].id == POLICY_ID
    assert page.metadata["provider_id"] == PROVIDER_ID
    assert client.calls[0][1] == (
        "providers",
        "openrouter",
        "models",
        "governance",
    )


def test_provider_governance_rejects_unsupported_mutation(client_factory):
    """Provider-scoped governance has no mutation route in Endeavor."""
    client = client_factory()
    policies = GovernancePolicies(client, provider=PROVIDER_ID)

    with pytest.raises(
        ValueError,
        match="provider-scoped governance supports listing only",
    ):
        policies.create(
            GovernancePolicyCreate(
                name="Default",
                policy_type="model",
                constraints={"allowed": True},
            )
        )

    assert client.calls == []


def test_invalid_governance_bodies_fail_before_request(client_factory):
    """Invalid Governance requests never reach the client."""
    client = client_factory()
    policies = GovernancePolicies(client)

    with pytest.raises(
        TypeError,
        match="invalid GovernancePolicyCreate fields",
    ):
        policies.create(
            name="Default",
            policy_type="unknown",
            constraints={"allowed": True},
        )

    with pytest.raises(
        TypeError,
        match="invalid GovernancePolicyPatch fields",
    ):
        policies.patch(POLICY_ID, name="")

    assert client.calls == []
