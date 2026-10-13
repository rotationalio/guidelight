import pytest
from pydantic import ValidationError

from guidelight import models as model_types


def test_test_case_update_rejects_create_only_parent_fields():
    for field in ("task_id", "experiment_id"):
        with pytest.raises(ValidationError):
            model_types.TestCaseUpdate(
                title="Greeting",
                **{field: "parent-1"},
            )


def test_nested_metric_options_and_test_case_version_urls_are_typed():
    metric = model_types.Metric.from_dict(
        {
            "options": [{"label": "Pass", "value": 1.0, "icon": "check"}],
        }
    )
    case = model_types.TestCase.from_dict(
        {
            "versions": [
                {
                    "version": 2,
                    "url": "/v2/testcases/case-1/versions/2",
                }
            ],
        }
    )

    assert isinstance(metric.options[0], model_types.MetricOption)
    assert metric.options[0].label == "Pass"
    assert isinstance(
        case.versions[0],
        model_types.TestCaseVersionURL,
    )
    assert case.versions[0].version == 2


def test_test_case_decodes_latest_version_and_attachments():
    case = model_types.TestCase.from_dict(
        {
            "title": "Greeting",
            "latest": {
                "version": 2,
                "context": {"context": "Hello"},
                "attachments": [{"name": "example.txt", "url": "/media/1"}],
            },
        }
    )
    assert case.latest.version == 2
    assert case.latest.attachments[0].name == "example.txt"
