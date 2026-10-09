import pytest

from guidelight.models import CommentCreate, Metric
from guidelight.resources import Comments, Generations, PageInfo

from .shared import (
    EXPERIMENT_ID,
    FakeClient,
    GENERATION_ID,
    METRIC_ID,
    RELEASE_ID,
    TASK_ID,
    TEST_CASE_ID,
)


def test_generation_filter_and_scoped_comments():
    client = FakeClient([{"page": {}, "generations": []}])
    Generations(client).list(release_id=RELEASE_ID)
    assert client.calls[0][2]["release_id"] == RELEASE_ID
    with pytest.raises(ValueError):
        Generations(client).list(experiment_id="e", release_id="r")

    client = FakeClient([{"id": "comment-1", "content": "Looks good"}])
    Comments(client, "experiments", EXPERIMENT_ID).create(
        CommentCreate(content="Looks good")
    )
    assert client.calls[0][1] == (
        "experiments",
        EXPERIMENT_ID,
        "comments",
    )


def test_generation_get_and_delete_routes():
    client = FakeClient([{"id": GENERATION_ID, "title": "Generation"}])
    generations = Generations(client)

    generation = generations.get(GENERATION_ID)
    generations.delete(GENERATION_ID)

    assert generation.id == GENERATION_ID
    assert client.calls == [
        ("GET", ("generations", GENERATION_ID), None),
        ("DELETE", ("generations", GENERATION_ID), {}),
    ]


def test_generation_metrics_decodes_typed_page():
    client = FakeClient(
        [
            {
                "page": {"page_size": 25, "offset": 5},
                "metrics": [
                    {
                        "id": METRIC_ID,
                        "name": "Correctness",
                        "value": 0.75,
                    },
                ],
            },
        ]
    )

    page = Generations(client).metrics(GENERATION_ID)

    assert client.calls == [
        ("GET", ("generations", GENERATION_ID, "metrics"), None),
    ]
    assert page.page_info == PageInfo(page_size=25, offset=5)
    assert isinstance(page.items[0], Metric)
    assert page.items[0].value == 0.75


def test_generation_actions_use_generation_scope():
    client = FakeClient(
        [
            {"success": True, "generation_id": GENERATION_ID},
            {"ok": True},
            {"page": {}, "comments": []},
        ]
    )
    generations = Generations(client)

    feedback = generations.feedback(
        GENERATION_ID,
        scores={METRIC_ID: 1.0},
    )
    generations.set_golden(GENERATION_ID, [TEST_CASE_ID])
    generations.comments(GENERATION_ID).list()

    assert feedback.generation_id == GENERATION_ID
    assert client.calls[0][1] == (
        "generations",
        GENERATION_ID,
        "feedback",
    )
    assert client.calls[1][1] == (
        "generations",
        GENERATION_ID,
        "golden",
    )
    assert client.calls[2][1] == (
        "generations",
        GENERATION_ID,
        "comments",
    )


def test_generation_can_be_saved_as_a_task_associated_test_case():
    client = FakeClient([{"id": TEST_CASE_ID, "title": "Saved Generation output"}])

    test_case = Generations(client).create_test_case(
        GENERATION_ID,
        task_ids=[TASK_ID],
        name="Saved Generation output",
    )

    assert test_case.id == TEST_CASE_ID
    assert client.calls == [
        (
            "POST",
            ("generations", GENERATION_ID, "testcase"),
            {
                "task_ids": [TASK_ID],
                "name": "Saved Generation output",
                "from_input": False,
            },
            {},
        ),
    ]
