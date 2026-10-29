import pytest
from pydantic import ValidationError

from guidelight import models as model_types


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
