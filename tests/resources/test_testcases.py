import io
from unittest.mock import Mock

import pytest
from requests import Response
from werkzeug.wrappers import Response as WerkzeugResponse

from guidelight.client import Client
from guidelight.exceptions import InvalidResponse
from guidelight.resources.testcases import TestCases as CaseManager
from guidelight.resources.testcases import TestCaseVersions as CaseVersionManager

from .shared import GENERATION_ID, TEST_CASE_ID


def test_test_case_parent_selection_is_exclusive(client):
    with pytest.raises(ValueError):
        CaseManager(
            client,
            task="task-1",
            experiment="experiment-1",
        )


def test_test_case_crud_golden_and_version_routes(client_factory):
    client = client_factory(
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


def test_set_golden_refreshes_test_case_after_empty_response(client_factory):
    client = client_factory(
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


def test_test_case_versions_require_a_test_case_ulid(client):
    with pytest.raises(ValueError):
        CaseVersionManager(
            client,
            "test-case-slug",
        )


def test_test_case_archive_upload_uses_multipart(client):
    archive = io.BytesIO(b"zip bytes")
    client.responses.append({"testcases": 1})

    result = CaseManager(client).upload_archive(
        archive,
        task_id="01JTASK",
    )

    method, endpoint, data, options = client.calls[0]
    assert method == "POST"
    assert endpoint == ("testcases", "upload")
    assert data == {"task_id": "01JTASK"}
    filename, uploaded_archive, content_type = options["files"]["file"]
    assert filename == "testcases.zip"
    assert uploaded_archive is archive
    assert content_type == "application/zip"
    assert result.testcases == 1


def test_test_case_archive_download_streams_response(client):
    response = Response()
    response.status_code = 200
    response.headers["Content-Type"] = "application/zip"
    response._content = b"zip bytes"
    response._content_consumed = True
    response.close = Mock(wraps=response.close)
    client.responses.append(response)
    destination = io.BytesIO()

    written = CaseManager(client).download_archive(
        destination,
        task="task-slug",
    )

    assert written == len(b"zip bytes")
    assert destination.getvalue() == b"zip bytes"
    response.close.assert_called_once_with()
    assert client.calls == [
        (
            "POST",
            ("testcases", "download"),
            None,
            {
                "query": {"task": "task-slug"},
                "stream": True,
                "raw": True,
            },
        )
    ]


def test_test_case_archive_download_rejects_non_zip_and_closes_response(client):
    response = Response()
    response.status_code = 200
    response.headers["Content-Type"] = "application/json"
    response._content = b'{"error":"not an archive"}'
    response._content_consumed = True
    response.close = Mock(wraps=response.close)
    client.responses.append(response)

    with pytest.raises(
        InvalidResponse,
        match="test case archive response must be application/zip",
    ):
        CaseManager(client).download_archive(
            io.BytesIO(),
            task="task-slug",
        )

    response.close.assert_called_once_with()


def test_test_case_archive_download_sends_query_parameters(httpserver):
    def check_request(request):
        assert request.args.to_dict(flat=False) == {"task": ["task-slug"]}
        assert request.get_data() == b""
        return WerkzeugResponse(
            b"zip bytes",
            status=200,
            content_type="application/zip",
        )

    httpserver.expect_request(
        "/v1/authenticate",
        method="POST",
    ).respond_with_json(
        {
            "access_token": "access",
            "refresh_token": "refresh",
        }
    )
    httpserver.expect_request(
        "/v2/testcases/download",
        method="POST",
    ).respond_with_handler(check_request)
    sdk_client = Client(
        httpserver.url_for(""),
        client_id="id",
        client_secret="secret",
        auth_url=httpserver.url_for(""),
    )
    destination = io.BytesIO()

    written = CaseManager(sdk_client).download_archive(
        destination,
        task="task-slug",
    )

    assert written == len(b"zip bytes")
    assert destination.getvalue() == b"zip bytes"


def test_test_case_render_forwards_renderer_and_prompts(client):
    client.responses.append(
        {
            "messages": [{"role": "user", "content": "Hello, world!"}],
            "renderer": "sprintf",
            "error": "",
        }
    )

    rendered = CaseManager(client).render(
        test_case=TEST_CASE_ID,
        renderer="sprintf",
        prompts=[
            {
                "index": 0,
                "role": "user",
                "template": "Hello, {{ name }}!",
            }
        ],
    )

    assert rendered.error == ""
    assert rendered.messages[0].content == "Hello, world!"
    assert client.calls == [
        (
            "POST",
            ("testcases", TEST_CASE_ID, "render"),
            {
                "renderer": "sprintf",
                "prompts": [
                    {
                        "index": 0,
                        "role": "user",
                        "template": "Hello, {{ name }}!",
                    }
                ],
            },
            {},
        )
    ]


def test_test_case_render_exposes_template_error_from_success_response(client):
    client.responses.append(
        {
            "messages": None,
            "renderer": "unknown",
            "error": "template: invalid syntax",
        }
    )

    rendered = CaseManager(client).render(
        test_case=TEST_CASE_ID,
        renderer="go",
        prompts=[
            {
                "index": 0,
                "role": "user",
                "template": "{{ invalid",
            }
        ],
    )

    assert rendered.error == "template: invalid syntax"
    assert rendered.messages == []


def test_test_case_version_render_uses_selected_version(client):
    client.responses.append(
        {
            "messages": [{"role": "user", "content": "Hello from version 2!"}],
            "renderer": "go",
            "error": "",
        }
    )

    rendered = CaseVersionManager(client, TEST_CASE_ID).render(
        2,
        renderer="go",
        prompts=[
            {
                "index": 0,
                "role": "user",
                "template": "Hello from version {{ version }}!",
            }
        ],
    )

    assert rendered.error == ""
    assert rendered.messages[0].content == "Hello from version 2!"
    assert client.calls == [
        (
            "POST",
            ("testcases", TEST_CASE_ID, "versions", "2", "render"),
            {
                "renderer": "go",
                "prompts": [
                    {
                        "index": 0,
                        "role": "user",
                        "template": "Hello from version {{ version }}!",
                    }
                ],
            },
            {},
        )
    ]
