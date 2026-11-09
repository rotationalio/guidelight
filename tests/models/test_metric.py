import pytest
from pydantic import ValidationError

from guidelight.models import MetricCreate, MetricUpdate


def test_metric_requests_serialize_writable_fields_and_reject_readonly_fields():
    create = MetricCreate(
        name="Correctness",
        description="Correctness score.",
        scoring="numeric",
        options=[{"label": "Pass", "value": 1.0}],
    )
    update = MetricUpdate(
        name="Correctness",
        description="Updated score.",
        scoring="numeric",
    )

    assert create.to_dict()["options"] == [{"label": "Pass", "value": 1.0}]
    assert update.to_dict()["description"] == "Updated score."

    for request_type in (
        MetricCreate,
        MetricUpdate,
    ):
        with pytest.raises(ValidationError):
            request_type(
                name="Correctness",
                scoring="numeric",
                value=1.0,
            )
