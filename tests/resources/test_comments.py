from guidelight.resources import Comments

from .shared import (
    COMMENT_ID_1,
    COMMENT_ID_2,
    EXPERIMENT_ID,
    FakeClient,
    GENERATION_ID,
)


def test_comment_update_delete_for_experiment_and_generation_parents():
    client = FakeClient(
        [
            {
                "id": COMMENT_ID_1,
                "content": "Updated experiment comment",
            },
            {
                "id": COMMENT_ID_2,
                "content": "Updated generation comment",
            },
        ]
    )
    experiment_comments = Comments(client, "experiments", EXPERIMENT_ID)
    generation_comments = Comments(client, "generations", GENERATION_ID)

    experiment_comment = experiment_comments.update(
        COMMENT_ID_1,
        content="Updated experiment comment",
    )
    experiment_comments.delete(COMMENT_ID_1)
    generation_comment = generation_comments.update(
        COMMENT_ID_2,
        content="Updated generation comment",
    )
    generation_comments.delete(COMMENT_ID_2)

    assert experiment_comment.content == "Updated experiment comment"
    assert generation_comment.content == "Updated generation comment"
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
        (
            "PUT",
            ("generations", GENERATION_ID, "comments", COMMENT_ID_2),
            {"content": "Updated generation comment"},
            {},
        ),
        (
            "DELETE",
            ("generations", GENERATION_ID, "comments", COMMENT_ID_2),
            {},
        ),
    ]
