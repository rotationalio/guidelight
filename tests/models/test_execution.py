from datetime import datetime

import pytest
from pydantic import ValidationError

from guidelight.models.execution import (
    ExecutionAttachment,
    ExecutionResult,
)


def test_execution_result_decodes_execution_output():
    result = ExecutionResult.from_dict(
        {
            "usage": {
                "invocations": 1,
                "input_tokens": 12,
                "output_tokens": 4,
                "total_tokens": 16,
            },
            "model": {
                "slug": "google/gemini-2.5-flash-image",
                "parameters": {"temperature": 0.2},
            },
            "output": {"caption": "A blue circle."},
            "mime_type": "application/json",
            "capabilities": ["image_generation"],
            "started": "2026-11-02T12:00:00Z",
            "finished": "2026-11-02T12:00:01Z",
            "outcome": "succeeded",
            "Attachments": [
                {
                    "filename": "circle.png",
                    "content_type": "image/png",
                    "data": b"png bytes",
                }
            ],
        }
    )

    assert result.usage.invocations == 1
    assert result.usage.total_tokens == 16
    assert result.model.slug == "google/gemini-2.5-flash-image"
    assert result.model.parameters == {"temperature": 0.2}
    assert result.output == {"caption": "A blue circle."}
    assert result.started == datetime.fromisoformat("2026-11-02T12:00:00+00:00")
    assert result.outcome == "succeeded"
    assert result.attachments == [
        ExecutionAttachment(
            filename="circle.png",
            content_type="image/png",
            data=b"png bytes",
        )
    ]


def test_execution_result_requires_execution_envelope_fields():
    with pytest.raises(ValidationError):
        ExecutionResult.from_dict({"answer": 42})


def test_execution_result_normalizes_null_collections():
    result = ExecutionResult.from_dict(
        {
            "usage": {},
            "model": {},
            "capabilities": None,
            "outcome": "failed",
            "Attachments": None,
        }
    )

    assert result.capabilities == []
    assert result.attachments == []
