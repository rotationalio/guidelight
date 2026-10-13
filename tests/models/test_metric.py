import pytest
from pydantic import ValidationError

from guidelight import models as model_types


def test_metric_requests_serialize_writable_fields_and_reject_readonly_fields():
    create = model_types.MetricCreate(
        name="Correctness",
        description="Correctness score.",
        scoring="numeric",
        options=[{"label": "Pass", "value": 1.0}],
    )
    update = model_types.MetricUpdate(
        name="Correctness",
        description="Updated score.",
        scoring="numeric",
    )

    assert create.to_dict()["options"] == [{"label": "Pass", "value": 1.0}]
    assert update.to_dict()["description"] == "Updated score."

    for request_type in (
        model_types.MetricCreate,
        model_types.MetricUpdate,
    ):
        with pytest.raises(ValidationError):
            request_type(
                name="Correctness",
                scoring="numeric",
                value=1.0,
            )
