import pytest

from guidelight.resources import Comments

from .shared import (
    COMMENT_ID_1,
    EXPERIMENT_ID,
    GENERATION_ID,
)


def test_comments_list_for_experiment_parent(client_factory):
    client = client_factory(
        [
            {
                "page": {},
                "comments": [
                    {
                        "id": COMMENT_ID_1,
                        "content": "Experiment comment",
                    }
                ],
            },
        ]
    )
    experiment_comments = Comments(client, "experiments", EXPERIMENT_ID)

    page = experiment_comments.list(page_size=25)

    assert page.items[0].content == "Experiment comment"
    assert client.calls == [
        (
            "GET",
            ("experiments", EXPERIMENT_ID, "comments"),
            {"page_size": 25, "offset": 0},
        ),
    ]


def test_comments_reject_generation_scope(client):
    """Generation comments require user claims and are not exposed by the SDK."""
    with pytest.raises(ValueError, match="comments support only experiments"):
        Comments(client, "generations", GENERATION_ID)
