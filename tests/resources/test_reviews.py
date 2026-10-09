from guidelight.resources import Experiments

from .shared import EXPERIMENT_ID, FakeClient, USER_ID


def test_experiment_association_and_review_scope():
    client = FakeClient(
        [
            {"id": "experiment-1", "name": "Eval"},
            {"page": {}, "reviews": []},
            {"success": True},
        ]
    )
    experiments = Experiments(client)

    experiments.capabilities(
        "experiment-1",
        [{"type": "integration_tool", "id": "tool-1"}],
    )
    experiments.reviews(EXPERIMENT_ID).list()
    experiments.reviews(EXPERIMENT_ID).invite([USER_ID])

    assert client.calls[0][1] == (
        "experiments",
        "experiment-1",
        "capabilities",
    )
    assert client.calls[0][2] == [{"type": "integration_tool", "id": "tool-1"}]
    assert client.calls[1][1] == (
        "experiments",
        EXPERIMENT_ID,
        "reviews",
    )
    assert client.calls[2][1] == ("reviews", "batch")


def test_review_invite_normalizes_empty_created_response():
    client = FakeClient([b""])
    reviews = Experiments(client).reviews(EXPERIMENT_ID)

    result = reviews.invite([USER_ID])

    assert result is None
    assert client.calls == [
        (
            "POST",
            ("reviews", "batch"),
            {
                "experiment_id": EXPERIMENT_ID,
                "reviewers": [USER_ID],
            },
            {},
        ),
    ]


def test_review_delete_uses_review_route():
    client = FakeClient()

    Experiments(client).reviews(EXPERIMENT_ID).delete(USER_ID)

    assert client.calls == [
        ("DELETE", ("reviews", USER_ID), {}),
    ]
