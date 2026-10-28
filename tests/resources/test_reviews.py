from guidelight.resources import Experiments

from .shared import EXPERIMENT_ID, REVIEW_ID


def test_experiment_association_and_review_scope(client_factory):
    client = client_factory(
        [
            {"id": "experiment-1", "name": "Eval"},
            {"page": {}, "reviews": []},
        ]
    )
    experiments = Experiments(client)

    experiments.capabilities(
        "experiment-1",
        [{"type": "integration_tool", "id": "tool-1"}],
    )
    experiments.reviews(EXPERIMENT_ID).list()

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


def test_review_delete_uses_review_route(client):
    Experiments(client).reviews(EXPERIMENT_ID).delete(REVIEW_ID)

    assert client.calls == [
        ("DELETE", ("reviews", REVIEW_ID), {}),
    ]


def test_reviews_do_not_expose_user_claim_invitation(client):
    reviews = Experiments(client).reviews(EXPERIMENT_ID)

    assert not hasattr(reviews, "invite")
