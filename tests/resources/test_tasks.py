from guidelight.models import TaskCreate
from guidelight.resources import Agents, PageInfo
from guidelight.resources.testcases import TestCases as CaseManager

from .shared import FakeClient, TASK_ID


def test_task_creation_is_agent_scoped():
    client = FakeClient([{"id": "task-1", "name": "Summarize"}])
    Agents(client).tasks("agent-1").create(
        TaskCreate(name="Summarize", description="Summarize text.")
    )
    assert client.calls[0][0:2] == (
        "POST",
        ("agents", "agent-1", "tasks"),
    )


def test_task_list_get_update_and_delete_routes():
    client = FakeClient(
        [
            {"page": {"page_size": 10, "offset": 0}, "tasks": []},
            {"id": TASK_ID, "name": "Summarize"},
            {"id": TASK_ID, "name": "Updated"},
        ]
    )
    tasks = Agents(client).tasks("agent-1")

    page = tasks.list(page_size=10)
    task = tasks.get(TASK_ID)
    updated = tasks.update(
        TASK_ID,
        name="Updated",
        description="Updated description.",
    )
    tasks.delete(TASK_ID)

    assert page.page_info == PageInfo(page_size=10, offset=0)
    assert task.id == TASK_ID
    assert updated.name == "Updated"
    assert client.calls == [
        (
            "GET",
            ("agents", "agent-1", "tasks"),
            {"offset": 0, "page_size": 10},
        ),
        ("GET", ("tasks", TASK_ID), None),
        (
            "PUT",
            ("tasks", TASK_ID),
            {
                "name": "Updated",
                "description": "Updated description.",
            },
            {},
        ),
        ("DELETE", ("tasks", TASK_ID), {}),
    ]


def test_task_crud_accepts_slug_references():
    client = FakeClient(
        [
            {"id": TASK_ID, "name": "Summarize", "slug": "summarize"},
            {"id": TASK_ID, "name": "Updated", "slug": "summarize"},
        ]
    )
    tasks = Agents(client).tasks("agent-1")

    task = tasks.get("summarize")
    updated = tasks.update(
        "summarize",
        name="Updated",
        description="Updated description.",
    )
    tasks.delete("summarize")

    assert task.slug == "summarize"
    assert updated.name == "Updated"
    assert client.calls == [
        ("GET", ("tasks", "summarize"), None),
        (
            "PUT",
            ("tasks", "summarize"),
            {
                "name": "Updated",
                "description": "Updated description.",
            },
            {},
        ),
        ("DELETE", ("tasks", "summarize"), {}),
    ]


def test_parent_scoped_experiment_metric_and_test_case_routes():
    client = FakeClient(
        [
            {"id": "experiment-1", "name": "Eval"},
            {"id": "metric-1", "name": "Correctness"},
            {"page": {}, "testcases": []},
        ]
    )
    tasks = Agents(client).tasks("agent-1")
    tasks.experiments("task-1").create(name="Eval")
    tasks.metrics("task-1").create(name="Correctness", scoring="numeric")
    CaseManager(client, task="task-1").list(input_modality="text")
    assert client.calls[0][1] == ("tasks", "task-1", "experiments")
    assert client.calls[1][1] == ("tasks", "task-1", "metrics")
    assert client.calls[2][1] == ("tasks", "task-1", "testcases")
