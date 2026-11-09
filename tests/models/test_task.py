import pytest
from pydantic import ValidationError

from guidelight.models import MetricCreate, Task, TaskCreate, TaskUpdate


def test_task_response_keeps_read_only_fields_out_of_requests():
    task = Task.from_dict(
        {
            "id": "task-1",
            "name": "Summarize",
            "description": "Summarize text.",
            "status": "ready",
            "counts": {"releases": 2},
            "usage": {"invocations": 5},
        }
    )
    assert task.id == "task-1"
    assert task.counts.releases == 2
    assert not hasattr(task, "to_dict")


def test_task_requests_serialize_metrics_only_on_create():
    metric = MetricCreate(
        name="Correctness",
        scoring="numeric",
    )
    create = TaskCreate(
        name="Summarize",
        description="Summarize text.",
        metrics=[metric],
    )
    update = TaskUpdate(
        name="Summarize",
        description="Updated description.",
    )

    assert create.to_dict()["metrics"] == [
        {
            "name": "Correctness",
            "description": "",
            "scoring": "numeric",
            "options": [],
        },
    ]
    assert "metrics" not in update.to_dict()

    with pytest.raises(ValidationError):
        TaskUpdate(
            name="Summarize",
            description="Updated description.",
            metrics=[metric],
        )
