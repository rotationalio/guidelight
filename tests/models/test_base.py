from datetime import datetime, timezone

import pytest

from guidelight.models import (
    BAO,
    Comment,
    Generation,
    Media,
    Metric,
    Release,
    ReleaseUpdate,
    Review,
    Task,
    TestCase as Case,
    TestCaseVersion as CaseVersion,
)


@pytest.mark.parametrize(
    ("model_type", "timestamp_fields"),
    [
        (BAO, ("created", "modified")),
        (Comment, ("created", "modified")),
        (Generation, ("created", "modified", "started")),
        (Media, ("created", "modified")),
        (Metric, ("created", "modified")),
        (
            Release,
            ("created", "modified", "deployed_on", "retired_on"),
        ),
        (ReleaseUpdate, ("deployed_on", "retired_on")),
        (Review, ("created", "modified")),
        (Task, ("created", "modified")),
        (Case, ("created", "modified")),
        (CaseVersion, ("created",)),
    ],
)
def test_resource_timestamps_parse_rfc3339(model_type, timestamp_fields):
    timestamp = "2026-10-07T20:30:00Z"
    expected = datetime(2026, 10, 7, 20, 30, tzinfo=timezone.utc)

    model = model_type.model_validate({field: timestamp for field in timestamp_fields})

    for field in timestamp_fields:
        assert getattr(model, field) == expected
