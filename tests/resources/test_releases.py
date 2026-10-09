import pytest
from pydantic import ValidationError

from guidelight.models import ReleaseCreate, ReleaseTest
from guidelight.resources import Releases

from .shared import (
    EXPERIMENT_ID,
    FakeClient,
    GENERATION_ID,
    RELEASE_ID,
    TASK_ID,
)


def test_release_create_and_clone_preserve_all_releases():
    responses = [
        {"releases": [{"id": "release-1"}, {"id": "release-2"}]},
        {"releases": [{"id": "clone-1"}, {"id": "clone-2"}]},
    ]
    client = FakeClient(responses)
    releases = Releases(client)
    created = releases.create(
        ReleaseCreate(
            experiment_id="exp-1",
            environments=["a", "b"],
            version="1.0.0",
            task_id="task-1",
        )
    )
    cloned = releases.clone(RELEASE_ID, ["staging", "production"])
    assert [item.id for item in created] == ["release-1", "release-2"]
    assert [item.id for item in cloned] == ["clone-1", "clone-2"]


@pytest.mark.parametrize("action", ["create", "clone"])
@pytest.mark.parametrize(
    "body",
    [
        {},
        {"releases": {"id": "release-1"}},
        {"releases": [{"id": "release-1"}, "not-an-object"]},
    ],
    ids=["missing-releases", "non-list-releases", "non-object-entry"],
)
def test_release_multi_result_actions_reject_malformed_envelopes(action, body):
    client = FakeClient([body])
    releases = Releases(client)

    with pytest.raises(TypeError):
        if action == "create":
            releases.create(
                ReleaseCreate(
                    experiment_id=EXPERIMENT_ID,
                    environments=["production"],
                    version="1.0.0",
                )
            )
        else:
            releases.clone(RELEASE_ID, ["production"])

    assert len(client.calls) == 1


def test_release_lifecycle_uses_documented_action_paths():
    client = FakeClient(
        [
            {"id": "release-1", "is_deployed": True},
            {"id": "release-1", "is_retired": True},
            {"output_text": "ok"},
        ]
    )
    releases = Releases(client)
    releases.deploy(RELEASE_ID)
    releases.retire(RELEASE_ID)
    result = releases.test(RELEASE_ID, ReleaseTest(input="hello"))
    assert client.calls[0][1] == ("releases", RELEASE_ID, "deploy")
    assert client.calls[1][1] == ("releases", RELEASE_ID, "retire")
    assert client.calls[2][1] == ("releases", RELEASE_ID, "test")
    assert result.output_text == "ok"


def test_task_scoped_release_create_and_release_generation_list():
    client = FakeClient(
        [
            {"releases": [{"id": RELEASE_ID, "task_id": TASK_ID}]},
            {
                "page": {"page_size": 5, "offset": 0},
                "generations": [{"id": GENERATION_ID}],
            },
        ]
    )
    releases = Releases(client, task=TASK_ID)

    created = releases.create(
        experiment_id=EXPERIMENT_ID,
        environments=["production"],
        version="1.0.0",
    )
    generations = releases.generations(RELEASE_ID).list(page_size=5)

    assert created[0].id == RELEASE_ID
    assert generations.items[0].id == GENERATION_ID
    assert client.calls[0][0:2] == (
        "POST",
        ("tasks", TASK_ID, "releases"),
    )
    assert client.calls[1] == (
        "GET",
        ("releases", RELEASE_ID, "generations"),
        {"offset": 0, "page_size": 5},
    )


def test_request_models_reject_response_only_fields():
    with pytest.raises(ValidationError):
        ReleaseCreate(
            experiment_id="experiment-1",
            environments=["production"],
            version="1.0.0",
            is_deployed=True,
        )
