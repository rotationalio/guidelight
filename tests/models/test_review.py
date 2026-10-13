from guidelight import models as model_types


def test_review_decodes_progress_fields():
    review = model_types.Review.from_dict(
        {
            "completed": 3,
            "total": 4,
            "percent": 75.0,
            "progress": "3 of 4",
        }
    )

    assert review.completed == 3
    assert review.total == 4
    assert review.percent == 75.0
    assert review.progress == "3 of 4"
