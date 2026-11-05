import pytest
from pydantic import ValidationError

from guidelight.models import Media, Metric, MetricOption, RenderedPrompt
from guidelight.models import TestCase as Case
from guidelight.models import TestCaseArchiveRequest as CaseArchiveRequest
from guidelight.models import TestCaseCreate as CaseCreate
from guidelight.models import TestCaseUpdate as CaseUpdate
from guidelight.models import TestCaseVersionURL as CaseVersionURL


def test_test_case_update_rejects_create_only_parent_fields():
    for field in ("task_id", "experiment_id"):
        with pytest.raises(ValidationError):
            CaseUpdate(
                title="Greeting",
                **{field: "parent-1"},
            )


@pytest.mark.parametrize("model_type", [CaseCreate, CaseUpdate])
def test_test_case_requests_use_typed_input_modalities(model_type):
    request = model_type(
        title="Greeting",
        context="Hello",
        context_type="text/plain",
        input_modality=["Text", "Image"],
    )

    assert request.to_dict()["input_modality"] == ["Text", "Image"]

    with pytest.raises(ValidationError):
        model_type(
            title="Greeting",
            input_modality=["PDF"],
        )


def test_nested_metric_options_and_test_case_version_urls_are_typed():
    metric = Metric.from_dict(
        {
            "options": [{"label": "Pass", "value": 1.0, "icon": "check"}],
        }
    )
    case = Case.from_dict(
        {
            "versions": [
                {
                    "version": 2,
                    "url": "/v2/testcases/case-1/versions/2",
                }
            ],
        }
    )

    assert isinstance(metric.options[0], MetricOption)
    assert metric.options[0].label == "Pass"
    assert isinstance(
        case.versions[0],
        CaseVersionURL,
    )
    assert case.versions[0].version == 2


def test_test_case_decodes_latest_version_and_attachments():
    case = Case.from_dict(
        {
            "title": "Greeting",
            "latest": {
                "version": 2,
                "context": {"context": "Hello"},
                "context_type": "text/plain",
                "input_modality": ["Text"],
                "attachments": [
                    {
                        "id": "01JMEDIA",
                        "name": "example.txt",
                        "content_type": "text/plain",
                        "modality": ["Text"],
                        "file_size": 12,
                        "checksum": "abc",
                        "download_url": (
                            "https://example.test/v2/media/01JMEDIA/"
                            "download/example.txt"
                        ),
                    }
                ],
            },
        }
    )
    assert case.latest.version == 2
    assert case.latest.context_type == "text/plain"
    assert case.latest.input_modality == ["Text"]
    assert isinstance(case.latest.attachments[0], Media)
    assert case.latest.attachments[0].name == "example.txt"
    assert case.latest.attachments[0].download_url.endswith("/example.txt")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("agent", "agent-slug"),
        ("task", "task-slug"),
        ("experiment", "experiment-slug"),
        ("testcases", ["01ARZ3NDEKTSV4RRFFQ69G5FAY"]),
    ],
)
def test_test_case_archive_request_accepts_one_selector(field, value):
    request = CaseArchiveRequest(**{field: value})

    assert request.to_dict() == {field: value}


@pytest.mark.parametrize(
    "fields",
    [
        {},
        {"agent": "agent-slug", "task": "task-slug"},
        {"testcases": []},
    ],
)
def test_test_case_archive_request_requires_exactly_one_selector(fields):
    with pytest.raises(ValidationError):
        CaseArchiveRequest(**fields)


def test_rendered_prompt_decodes_messages_and_normalizes_error_response():
    rendered = RenderedPrompt.from_dict(
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "renderer": "go",
            "error": "",
        }
    )
    failed = RenderedPrompt.from_dict(
        {
            "messages": None,
            "renderer": "unknown",
            "error": "template error",
        }
    )

    assert rendered.messages[0].content == "Hello"
    assert failed.messages == []
    assert failed.error == "template error"
