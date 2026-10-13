import pytest
from pydantic import ValidationError

from guidelight import models as model_types


def test_release_update_requests_reject_response_only_fields():
    for request_type in (
        model_types.ReleaseUpdate,
        model_types.ReleasePatch,
    ):
        with pytest.raises(ValidationError):
            request_type(
                provider_id="provider-1",
                is_deployed=True,
            )


def test_release_create_has_only_writable_fields():
    request = model_types.ReleaseCreate(
        task_id="task-1",
        experiment_id="experiment-1",
        environments=["production", "staging"],
        version="1.2.3",
    )
    assert request.to_dict() == {
        "task_id": "task-1",
        "experiment_id": "experiment-1",
        "environments": ["production", "staging"],
        "version": "1.2.3",
    }


def test_release_create_and_clone_require_environments():
    with pytest.raises(ValidationError):
        model_types.ReleaseCreate(
            experiment_id="experiment-1",
            environments=[],
            version="1.0.0",
        )

    with pytest.raises(ValidationError):
        model_types.ReleaseClone(environments=[])


def test_release_patch_requires_at_least_one_change():
    with pytest.raises(ValidationError):
        model_types.ReleasePatch()

    assert model_types.ReleasePatch(provider_id="").to_dict() == {
        "provider_id": "",
    }
