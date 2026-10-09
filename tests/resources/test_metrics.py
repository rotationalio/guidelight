from guidelight.resources import Agents

from .shared import FakeClient, METRIC_ID, TASK_ID


def test_metric_list_get_update_and_delete_routes():
    client = FakeClient(
        [
            {
                "page": {},
                "metrics": [{"id": METRIC_ID, "name": "Correctness"}],
            },
            {"id": METRIC_ID, "name": "Correctness"},
            {"id": METRIC_ID, "name": "Updated Correctness"},
        ]
    )
    metrics = Agents(client).tasks("agent-1").metrics(TASK_ID)

    page = metrics.list()
    metric = metrics.get(METRIC_ID)
    updated = metrics.update(
        METRIC_ID,
        name="Updated Correctness",
        scoring="numeric",
    )
    metrics.delete(METRIC_ID)

    assert page.items[0].id == METRIC_ID
    assert metric.id == METRIC_ID
    assert updated.name == "Updated Correctness"
    assert client.calls[0] == (
        "GET",
        ("tasks", TASK_ID, "metrics"),
        {"offset": 0},
    )
    assert client.calls[1] == ("GET", ("metrics", METRIC_ID), None)
    assert client.calls[2][0:2] == ("PUT", ("metrics", METRIC_ID))
    assert client.calls[3] == ("DELETE", ("metrics", METRIC_ID), {})
