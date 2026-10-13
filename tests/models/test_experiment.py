import pytest
from pydantic import ValidationError

from guidelight import models as model_types

VALID_EXPERIMENT_UPDATE = {
    "name": "Evaluation",
    "context_type": "text/plain",
    "input_types": ["text/plain"],
    "input_modality": ["Text"],
    "output_types": ["text/plain"],
    "output_modality": ["Text"],
    "renderer": "go",
    "prompts": [{"role": "user", "content": "{{ context }}"}],
}


def test_experiment_generation_and_release_models_decode_nested_data():
    experiment = model_types.Experiment.from_dict(
        {
            "name": "Evaluation",
            "capabilities": [{"type": "integration_tool", "id": "tool-1"}],
        }
    )
    generation = model_types.Generation.from_dict(
        {
            "output_text": "result",
            "examples": [{"title": "Example"}],
        }
    )
    release = model_types.Release.from_dict(
        {
            "version": "1.2.3",
            "status": "Live",
            "is_deployed": True,
            "endpoint": "/api/a/t",
        }
    )
    assert experiment.capabilities[0]["id"] == "tool-1"
    assert generation.examples[0].title == "Example"
    assert release.is_deployed is True


def test_experiment_create_accepts_ready_status():
    request = model_types.ExperimentCreate(
        name="Ready Evaluation",
        status="ready",
    )

    assert request.to_dict()["status"] == "ready"


def test_experiment_decodes_unconfigured_draft():
    experiment = model_types.Experiment.model_validate(
        {
            "status": "draft",
            "input_types": None,
            "input_modality": None,
            "output_types": None,
            "output_modality": None,
            "renderer": "unknown",
            "prompts": None,
        }
    )

    assert experiment.input_types == []
    assert experiment.input_modality == []
    assert experiment.output_types == []
    assert experiment.output_modality == []
    assert experiment.renderer == "unknown"
    assert experiment.prompts == []


def test_experiment_request_rejects_unknown_renderer():
    with pytest.raises(ValidationError):
        model_types.ExperimentCreate(renderer="unknown")


@pytest.mark.parametrize(
    "missing_field",
    [
        "name",
        "input_modality",
        "output_types",
        "output_modality",
        "renderer",
        "prompts",
    ],
)
def test_experiment_update_requires_complete_put_fields(missing_field):
    fields = dict(VALID_EXPERIMENT_UPDATE)
    fields.pop(missing_field)

    with pytest.raises(ValidationError):
        model_types.ExperimentUpdate(**fields)


@pytest.mark.parametrize(
    "missing_field",
    ["context_type", "input_types"],
)
def test_experiment_update_requires_text_input_fields(missing_field):
    fields = dict(VALID_EXPERIMENT_UPDATE)
    fields.pop(missing_field)

    with pytest.raises(ValidationError):
        model_types.ExperimentUpdate(**fields)


def test_experiment_patch_serializes_only_supplied_fields():
    request = model_types.ExperimentPatch(description="Updated description")

    assert request.to_dict() == {
        "description": "Updated description",
    }


def test_experiment_patch_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        model_types.ExperimentPatch(usage={"requests": 1})
