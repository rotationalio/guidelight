import pytest

from guidelight.models import ExperimentCreate, ExperimentPatch
from guidelight.resources import Experiments

from .shared import EXPERIMENT_ID, FakeClient


def test_experiment_list_uses_task_scoped_route():
    client = FakeClient([{"page": {}, "experiments": []}])

    page = Experiments(client, task="task-1").list(page_size=10)

    assert page.items == []
    assert client.calls == [
        (
            "GET",
            ("tasks", "task-1", "experiments"),
            {"offset": 0, "page_size": 10},
        )
    ]


def test_unscoped_experiment_list_fails_before_request():
    client = FakeClient()

    with pytest.raises(
        ValueError,
        match="Experiment listing requires a Task manager",
    ):
        Experiments(client).list()

    assert client.calls == []


def test_experiment_create_decodes_unconfigured_draft_response():
    client = FakeClient(
        [
            {
                "id": EXPERIMENT_ID,
                "name": "Draft Evaluation",
                "status": "draft",
                "input_types": None,
                "input_modality": None,
                "output_types": None,
                "output_modality": None,
                "renderer": "unknown",
                "prompts": None,
            },
        ]
    )
    experiments = Experiments(client, task="task-1")

    experiment = experiments.create(ExperimentCreate(name="Draft Evaluation"))

    assert experiment.id == EXPERIMENT_ID
    assert experiment.input_types == []
    assert experiment.output_types == []
    assert experiment.renderer == "unknown"
    assert experiment.prompts == []
    assert client.calls == [
        (
            "POST",
            ("tasks", "task-1", "experiments"),
            {"name": "Draft Evaluation"},
            {},
        ),
    ]


def test_experiment_patch_validates_and_sends_partial_body():
    client = FakeClient(
        [
            {
                "id": EXPERIMENT_ID,
                "name": "Evaluation",
                "description": "Updated description",
            },
        ]
    )
    experiments = Experiments(client)

    patched = experiments.patch(
        "evaluation",
        ExperimentPatch(description="Updated description"),
    )

    assert patched.description == "Updated description"
    assert client.calls == [
        (
            "PATCH",
            ("experiments", "evaluation"),
            {"description": "Updated description"},
            {},
        ),
    ]


def test_experiment_patch_rejects_unknown_fields_before_request():
    client = FakeClient()

    with pytest.raises(TypeError):
        Experiments(client).patch(
            "evaluation",
            usage={"requests": 1},
        )

    assert client.calls == []


def test_experiment_get_update_delete_and_set_test_cases_routes():
    client = FakeClient(
        [
            {"id": EXPERIMENT_ID, "name": "Evaluation"},
            {"id": EXPERIMENT_ID, "name": "Updated Evaluation"},
            {"success": True},
        ]
    )
    experiments = Experiments(client)

    experiment = experiments.get(EXPERIMENT_ID)
    updated = experiments.update(
        EXPERIMENT_ID,
        name="Updated Evaluation",
        context_type="text/plain",
        input_types=["text/plain"],
        input_modality=["Text"],
        output_types=["text/plain"],
        output_modality=["Text"],
        renderer="go",
        prompts=[{"index": 0, "role": "user", "template": "{{ context }}"}],
    )
    experiments.delete(EXPERIMENT_ID)
    result = experiments.set_test_cases(EXPERIMENT_ID, ["version-1"])

    assert experiment.id == EXPERIMENT_ID
    assert updated.name == "Updated Evaluation"
    assert result == {"success": True}
    assert client.calls[0] == (
        "GET",
        ("experiments", EXPERIMENT_ID),
        None,
    )
    assert client.calls[1][0:2] == (
        "PUT",
        ("experiments", EXPERIMENT_ID),
    )
    assert client.calls[2] == (
        "DELETE",
        ("experiments", EXPERIMENT_ID),
        {},
    )
    assert client.calls[3] == (
        "POST",
        ("experiments", EXPERIMENT_ID, "testcases"),
        {"test_case_version_ids": ["version-1"]},
        {},
    )
