import pytest
from pydantic import ValidationError

from guidelight.models import Generation, GenerationTestCaseCreate


def test_generation_test_case_create_requires_tasks_and_serializes_fields():
    request = GenerationTestCaseCreate(
        task_ids=["task-1"],
        name="Saved output",
    )

    assert request.to_dict() == {
        "task_ids": ["task-1"],
        "name": "Saved output",
        "from_input": False,
    }

    with pytest.raises(ValidationError):
        GenerationTestCaseCreate(task_ids=[])


def test_generation_decodes_input_and_output_media():
    generation = Generation.from_dict(
        {
            "output_modality": ["Text", "Image"],
            "output_text": "Generated image",
            "input_attachments": [{"name": "input.png", "content_type": "image/png"}],
            "output_attachments": [
                {
                    "name": "output.png",
                    "content_type": "image/png",
                    "modality": ["Image"],
                }
            ],
        }
    )

    assert generation.output_modality == ["Text", "Image"]
    assert generation.attachments_included
    assert generation.input_attachments is not None
    assert generation.output_attachments is not None
    assert generation.input_attachments[0].content_type == "image/png"
    assert generation.output_attachments[0].modality == ["Image"]


def test_generation_distinguishes_omitted_from_included_empty_attachments():
    list_entry = Generation.from_dict({"id": "01JGENERATION"})
    detail = Generation.from_dict(
        {
            "id": "01JGENERATION",
            "input_attachments": [],
            "output_attachments": [],
        }
    )

    assert list_entry.input_attachments is None
    assert list_entry.output_attachments is None
    assert not list_entry.attachments_included
    assert detail.input_attachments == []
    assert detail.output_attachments == []
    assert detail.attachments_included
