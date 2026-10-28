"""Tests for governance policy models."""

import pytest
from pydantic import ValidationError

from guidelight.models import GovernancePolicyCreate, GovernancePolicyPatch


def test_governance_create_requires_policy_fields():
    """Governance creation requires a name, type, and constraints."""
    with pytest.raises(ValidationError):
        GovernancePolicyCreate(name="Default")


def test_governance_patch_serializes_only_supplied_fields():
    """Governance PATCH requests support partial updates."""
    request = GovernancePolicyPatch(active=False)

    assert request.to_dict() == {"active": False}


@pytest.mark.parametrize(
    "request_type, fields",
    [
        (
            GovernancePolicyCreate,
            {"name": "", "policy_type": "model", "constraints": {"x": 1}},
        ),
        (
            GovernancePolicyCreate,
            {
                "name": "Default",
                "policy_type": "unknown",
                "constraints": {"x": 1},
            },
        ),
        (
            GovernancePolicyCreate,
            {"name": "Default", "policy_type": "model", "constraints": {}},
        ),
        (
            GovernancePolicyCreate,
            {
                "name": "Default",
                "policy_type": "model",
                "constraints": object(),
            },
        ),
        (GovernancePolicyPatch, {"name": " "}),
        (GovernancePolicyPatch, {"policy_type": "unknown"}),
        (GovernancePolicyPatch, {"constraints": object()}),
    ],
)
def test_governance_requests_reject_invalid_server_bodies(
    request_type,
    fields,
):
    """Governance requests enforce names, policy types, and JSON values."""
    with pytest.raises(ValidationError):
        request_type(**fields)
