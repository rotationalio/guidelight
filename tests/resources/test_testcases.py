import pytest

from guidelight.resources.testcases import TestCases as CaseManager
from guidelight.resources.testcases import (
    TestCaseVersions as CaseVersionManager,
)

from .shared import FakeClient, GENERATION_ID, TEST_CASE_ID


def test_test_case_parent_selection_is_exclusive():
    with pytest.raises(ValueError):
        CaseManager(
            FakeClient(),
            task="task-1",
            experiment="experiment-1",
        )


def test_test_case_crud_golden_and_version_routes():
    client = FakeClient(
        [
            {"id": TEST_CASE_ID, "title": "Greeting"},
            {"id": TEST_CASE_ID, "title": "Updated Greeting"},
            {
                "id": TEST_CASE_ID,
                "title": "Updated Greeting",
                "golden_example": GENERATION_ID,
            },
            {"id": "version-2", "version": 2},
        ]
    )
    cases = CaseManager(client)

    created = cases.create(title="Greeting")
    updated = cases.update(TEST_CASE_ID, title="Updated Greeting")
    cases.delete(TEST_CASE_ID)
    golden = cases.set_golden(TEST_CASE_ID, GENERATION_ID)
    version = cases.versions(TEST_CASE_ID).get(2)
    cases.versions(TEST_CASE_ID).delete(2)

    assert created.id == TEST_CASE_ID
    assert updated.title == "Updated Greeting"
    assert golden.golden_example == GENERATION_ID
    assert version.version == 2
    assert client.calls == [
        (
            "POST",
            ("testcases",),
            {
                "title": "Greeting",
                "description": "",
                "attachments": [],
            },
            {},
        ),
        (
            "PUT",
            ("testcases", TEST_CASE_ID),
            {
                "title": "Updated Greeting",
                "description": "",
                "attachments": [],
            },
            {},
        ),
        ("DELETE", ("testcases", TEST_CASE_ID), {}),
        (
            "PUT",
            ("testcases", TEST_CASE_ID, "golden"),
            {"generation_id": GENERATION_ID},
            {},
        ),
        (
            "GET",
            ("testcases", TEST_CASE_ID, "versions", "2"),
            None,
        ),
        (
            "DELETE",
            ("testcases", TEST_CASE_ID, "versions", "2"),
            {},
        ),
    ]


def test_set_golden_refreshes_test_case_after_empty_response():
    client = FakeClient(
        [
            None,
            {
                "id": TEST_CASE_ID,
                "title": "Greeting",
                "golden_example": GENERATION_ID,
            },
        ]
    )

    golden = CaseManager(client).set_golden(TEST_CASE_ID, GENERATION_ID)

    assert golden.golden_example == GENERATION_ID
    assert client.calls == [
        (
            "PUT",
            ("testcases", TEST_CASE_ID, "golden"),
            {"generation_id": GENERATION_ID},
            {},
        ),
        ("GET", ("testcases", TEST_CASE_ID), None),
    ]


def test_test_case_versions_require_a_test_case_ulid():
    with pytest.raises(ValueError):
        CaseVersionManager(
            FakeClient(),
            "test-case-slug",
        )
