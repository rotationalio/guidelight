"""Tests for environment response and request models."""

import pytest
from pydantic import ValidationError

from guidelight.models import (
    Environment,
    EnvironmentCreate,
    EnvironmentPatch,
    EnvironmentUpdate,
)


def test_environment_decodes_rfc3339_timestamps():
    """Environment timestamps are parsed into datetime values."""
    environment = Environment.model_validate(
        {
            "id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "name": "Production",
            "created": "2026-01-01T12:00:00Z",
            "modified": "2026-01-02T12:00:00Z",
        }
    )

    assert environment.created is not None
    assert environment.modified is not None


def test_environment_requests_serialize_writable_fields():
    """Create and PUT requests emit only writable environment fields."""
    create = EnvironmentCreate(name="Staging", slug="staging")
    update = EnvironmentUpdate(name="Staging", slug="staging")

    assert create.to_dict()["name"] == "Staging"
    assert update.to_dict()["slug"] == "staging"


def test_empty_environment_patch_is_rejected():
    """An empty environment PATCH cannot be sent to Endeavor."""
    with pytest.raises(ValidationError):
        EnvironmentPatch()


@pytest.mark.parametrize(
    "request_type, fields",
    [
        (EnvironmentCreate, {"name": "", "slug": "staging"}),
        (EnvironmentCreate, {"name": "Staging", "slug": " "}),
        (EnvironmentUpdate, {"name": "", "slug": "staging"}),
        (EnvironmentPatch, {"name": ""}),
        (EnvironmentPatch, {"slug": " "}),
        (EnvironmentPatch, {"provider": {}}),
        (EnvironmentPatch, {"is_default": False}),
    ],
)
def test_environment_requests_reject_invalid_server_bodies(
    request_type,
    fields,
):
    """Environment requests enforce Endeavor's structural validation."""
    with pytest.raises(ValidationError):
        request_type(**fields)


def test_environment_provider_reference_serializes_its_id():
    """Environment write requests require the nested Provider identifier."""
    request = EnvironmentPatch(provider={"id": "01ARZ3NDEKTSV4RRFFQ69G5FAV"})

    assert request.to_dict()["provider"] == {"id": "01ARZ3NDEKTSV4RRFFQ69G5FAV"}
