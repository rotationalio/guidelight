import pytest

from guidelight.resources import Comments

from .shared import (
    COMMENT_ID_1,
    EXPERIMENT_ID,
    GENERATION_ID,
)


def test_comment_update_delete_for_experiment_parent(client_factory):
    client = client_factory(
        [
            {
                "id": COMMENT_ID_1,
                "content": "Updated experiment comment",
            },
        ]
    )
    experiment_comments = Comments(client, "experiments", EXPERIMENT_ID)

    experiment_comment = experiment_comments.update(
        COMMENT_ID_1,
        content="Updated experiment comment",
    )
    experiment_comments.delete(COMMENT_ID_1)

    assert experiment_comment.content == "Updated experiment comment"
    assert client.calls == [
        (
            "PUT",
            ("experiments", EXPERIMENT_ID, "comments", COMMENT_ID_1),
            {"content": "Updated experiment comment"},
            {},
        ),
        (
            "DELETE",
            ("experiments", EXPERIMENT_ID, "comments", COMMENT_ID_1),
            {},
        ),
    ]


def test_comments_reject_generation_scope(client):
    """Generation comments require user claims and are not exposed by the SDK."""
    with pytest.raises(ValueError, match="comments support only experiments"):
        Comments(client, "generations", GENERATION_ID)
