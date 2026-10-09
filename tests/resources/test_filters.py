"""Cross-resource tests for request validation, filtering, and list envelopes.

These tests live together because filtering is implemented by the shared
resource-manager infrastructure rather than by a dedicated ``filters.py``
resource module.
"""

import pytest
from pydantic import ValidationError

from guidelight.models import (
    GenerationFeedback,
    MetricCreate,
    MetricUpdate,
    ReleaseCreate,
    ReleasePatch,
)
from guidelight.resources import (
    Agents,
    Comments,
    Experiments,
    Generations,
    Releases,
)
from guidelight.resources.testcases import TestCases as CaseManager

from .shared import (
    EXPERIMENT_ID,
    GENERATION_ID,
    METRIC_ID,
    RELEASE_ID,
    TASK_ID,
    FakeClient,
)


def test_invalid_request_bodies_fail_before_request():
    client = FakeClient()
    metrics = Agents(client).tasks("agent-1").metrics("task-1")
    releases = Releases(client)
    generations = Generations(client)
    reviews = Experiments(client).reviews(EXPERIMENT_ID)

    with pytest.raises(ValidationError):
        metrics.create(MetricCreate(name="Correctness"))
    with pytest.raises(ValidationError):
        metrics.update(METRIC_ID, MetricUpdate(name="Correctness"))
    with pytest.raises(ValidationError):
        releases.create(
            ReleaseCreate(
                experiment_id=EXPERIMENT_ID,
                environments=[],
                version="1.0.0",
            )
        )
    with pytest.raises(ValidationError):
        releases.clone(RELEASE_ID, [])
    with pytest.raises(ValidationError):
        releases.patch(RELEASE_ID, ReleasePatch())
    with pytest.raises(ValidationError):
        reviews.invite([])
    with pytest.raises(ValidationError):
        generations.feedback(
            GENERATION_ID,
            GenerationFeedback(scores={}),
        )

    assert client.calls == []


def test_supported_resource_filters_are_forwarded():
    client = FakeClient(
        [
            {"page": {}, "testcases": []},
            {"page": {}, "experiments": []},
            {"page": {}, "generations": []},
            {"page": {}, "releases": []},
        ]
    )

    CaseManager(client).list(input_modality="Text")
    Experiments(client, task=TASK_ID).list(status="ready")
    Generations(client).list(release_id=RELEASE_ID)
    Releases(client).list(environment_id="production")

    assert client.calls[0][2]["input_modality"] == "Text"
    assert client.calls[1][2]["status"] == "ready"
    assert client.calls[2][2]["release_id"] == RELEASE_ID
    assert client.calls[3][2]["environment_id"] == "production"


@pytest.mark.parametrize(
    ("manager_factory", "filter_name", "filter_value"),
    [
        (
            lambda client: Experiments(client, task=TASK_ID),
            "agent_ids",
            ["agent-1"],
        ),
        (lambda client: Releases(client), "agent_id", "agent-1"),
        (lambda client: Releases(client), "agent_ids", ["agent-1"]),
    ],
)
def test_unimplemented_agent_filters_are_rejected(
    manager_factory,
    filter_name,
    filter_value,
):
    client = FakeClient()

    with pytest.raises(
        TypeError,
        match=rf"unsupported filter\(s\): {filter_name}",
    ):
        manager_factory(client).list(**{filter_name: filter_value})

    assert client.calls == []


@pytest.mark.parametrize(
    "manager_factory",
    [
        lambda client: Agents(client),
        lambda client: Agents(client).tasks("agent-1"),
        lambda client: CaseManager(client),
        lambda client: Experiments(client, task=TASK_ID),
        lambda client: Agents(client).tasks("agent-1").metrics(TASK_ID),
        lambda client: Generations(client),
        lambda client: Releases(client),
        lambda client: Comments(client, "experiments", EXPERIMENT_ID),
        lambda client: Experiments(client).reviews(EXPERIMENT_ID),
        lambda client: Releases(client).generations(RELEASE_ID),
    ],
)
def test_all_list_managers_reject_unsupported_filters(manager_factory):
    client = FakeClient()

    with pytest.raises(TypeError, match=r"unsupported filter\(s\): unknown"):
        manager_factory(client).list(unknown=True)

    assert client.calls == []


def test_nonuniform_list_envelope_metadata_is_preserved():
    client = FakeClient(
        [
            {
                "page": {},
                "testcases": [],
                "has_golden": True,
            },
            {
                "page": {},
                "generations": [],
                "experiment_id": EXPERIMENT_ID,
            },
            {
                "page": {},
                "generations": [],
                "release_id": RELEASE_ID,
            },
        ]
    )

    test_cases = CaseManager(client).list()
    experiment_generations = Generations(client).list(
        experiment_id=EXPERIMENT_ID,
    )
    release_generations = Generations(client).list(
        release_id=RELEASE_ID,
    )

    assert test_cases.metadata == {"has_golden": True}
    assert experiment_generations.metadata == {
        "experiment_id": EXPERIMENT_ID,
    }
    assert release_generations.metadata == {
        "release_id": RELEASE_ID,
    }


def test_ulid_only_routes_reject_slugs_before_request():
    client = FakeClient()

    with pytest.raises(ValueError):
        Releases(client).get("release-slug")
    with pytest.raises(ValueError):
        Generations(client).get("generation-slug")
    with pytest.raises(ValueError):
        CaseManager(client).get("test-case-slug")
    with pytest.raises(ValueError):
        Comments(client, "experiments", "experiment-slug")
    with pytest.raises(ValueError):
        Experiments(client).reviews("experiment-slug")

    assert client.calls == []
