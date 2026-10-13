import pytest
from pydantic import ValidationError

from guidelight import models as model_types


def test_generation_feedback_response_decodes_all_fields():
    response = model_types.GenerationFeedbackResponse.from_dict(
        {
            "success": True,
            "generation_id": "generation-1",
            "review_id": "review-1",
            "status": "completed",
            "completed": 2,
            "total": 2,
            "scores": {"metric-1": 0.75},
        }
    )

    assert response.success is True
    assert response.generation_id == "generation-1"
    assert response.review_id == "review-1"
    assert response.status == "completed"
    assert response.completed == 2
    assert response.total == 2
    assert response.scores == {"metric-1": 0.75}


def test_generation_test_case_create_requires_tasks_and_serializes_fields():
    request = model_types.GenerationTestCaseCreate(
        task_ids=["task-1"],
        name="Saved output",
    )

    assert request.to_dict() == {
        "task_ids": ["task-1"],
        "name": "Saved output",
        "from_input": False,
    }

    with pytest.raises(ValidationError):
        model_types.GenerationTestCaseCreate(task_ids=[])
