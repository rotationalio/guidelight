import pytest
from pydantic import ValidationError

from guidelight import models as model_types


def test_comment_decodes_replies_and_preserves_request_field_differences():
    comment = model_types.Comment.from_dict(
        {
            "content": "Parent",
            "replies": [{"content": "Reply", "reply_to": "comment-1"}],
        }
    )

    assert isinstance(comment.replies[0], model_types.Comment)
    assert comment.replies[0].content == "Reply"
    assert model_types.CommentCreate(
        content="Reply",
        reply_to="comment-1",
    ).to_dict() == {
        "content": "Reply",
        "reply_to": "comment-1",
    }

    with pytest.raises(ValidationError):
        model_types.CommentUpdate(
            content="Updated",
            reply_to="comment-1",
        )
