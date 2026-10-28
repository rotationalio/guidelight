import pytest

from guidelight.resources import Generations

from .shared import (
    GENERATION_ID,
    RELEASE_ID,
    TASK_ID,
    TEST_CASE_ID,
)


def test_generation_filters_are_forwarded_and_mutually_exclusive(client_factory):
    client = client_factory([{"page": {}, "generations": []}])
    Generations(client).list(release_id=RELEASE_ID)
    assert client.calls[0][2]["release_id"] == RELEASE_ID
    with pytest.raises(ValueError):
        Generations(client).list(experiment_id="e", release_id="r")


def test_generation_get_and_delete_routes(client_factory):
    client = client_factory([{"id": GENERATION_ID, "title": "Generation"}])
    generations = Generations(client)

    generation = generations.get(GENERATION_ID)
    generations.delete(GENERATION_ID)

    assert generation.id == GENERATION_ID
    assert client.calls == [
        ("GET", ("generations", GENERATION_ID), None),
        ("DELETE", ("generations", GENERATION_ID), {}),
    ]


@pytest.mark.parametrize("method_name", ["metrics", "feedback", "comments"])
def test_generation_manager_does_not_expose_user_claim_operations(
    client,
    method_name,
):
    """API-key-authenticated managers omit routes that require user claims."""
    assert not hasattr(Generations(client), method_name)


def test_generation_set_golden_uses_generation_scope(client_factory):
    client = client_factory([{"ok": True}])
    generations = Generations(client)

    generations.set_golden(GENERATION_ID, [TEST_CASE_ID])

    assert client.calls[0][1] == (
        "generations",
        GENERATION_ID,
        "golden",
    )


def test_generation_can_be_saved_as_a_task_associated_test_case(client_factory):
    client = client_factory([{"id": TEST_CASE_ID, "title": "Saved Generation output"}])

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
