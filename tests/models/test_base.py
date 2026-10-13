from datetime import datetime, timezone

import pytest

from guidelight import models as model_types


@pytest.mark.parametrize(
    ("model_type", "timestamp_fields"),
    [
        (model_types.BAO, ("created", "modified")),
        (model_types.Comment, ("created", "modified")),
        (model_types.Generation, ("created", "modified", "started")),
        (model_types.Metric, ("created", "modified")),
        (
            model_types.Release,
            ("created", "modified", "deployed_on", "retired_on"),
        ),
        (model_types.ReleaseUpdate, ("deployed_on", "retired_on")),
        (model_types.Review, ("created", "modified")),
        (model_types.Task, ("created", "modified")),
        (model_types.TestCase, ("created", "modified")),
        (model_types.TestCaseVersion, ("created",)),
        (model_types.TestCaseAttachment, ("created",)),
    ],
)
def test_resource_timestamps_parse_rfc3339(model_type, timestamp_fields):
    timestamp = "2026-10-07T20:30:00Z"
    expected = datetime(2026, 10, 7, 20, 30, tzinfo=timezone.utc)

    model = model_type.model_validate({field: timestamp for field in timestamp_fields})

    for field in timestamp_fields:
        assert getattr(model, field) == expected
