from guidelight.models import Comment


def test_comment_decodes_replies():
    comment = Comment.from_dict(
        {
            "content": "Parent",
            "replies": [{"content": "Reply", "reply_to": "comment-1"}],
        }
    )

    assert isinstance(comment.replies[0], Comment)
    assert comment.replies[0].content == "Reply"
