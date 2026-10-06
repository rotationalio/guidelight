import io
import json

import pytest
from pytest_httpserver import HTTPServer
from requests import Response as RequestsResponse
from werkzeug.wrappers import Response as WerkzeugResponse

from guidelight.client import Client
from guidelight.exceptions import (
    AuthenticationError,
    ClientError,
    NotFound,
    ServerError,
)
from guidelight.helpers import _format_response_error, _serialize_context


def test_preflight():
    """
    Test preflight authentication happens implicitly.
    """

    # Create a test server
    server = HTTPServer()
    server.start()

    # Expect authentication request
    server.expect_request("/v1/authenticate").respond_with_json(
        {
            "access_token": "access",
            "refresh_token": "refresh",
        }
    )

    base_url = f"http://localhost:{server.port}"

    # Start a guidelight client
    client = Client(
        f"http://localhost:{server.port}",
        client_id="id",
        client_secret="secret",
        auth_url=base_url,
    )

    # Perform auth required request to trigger the preflight code
    server.expect_request(
        "/v2/authrequired",
        headers={"Authorization": "Bearer access"},
    ).respond_with_json([])
    client.post({}, "/v2/authrequired")


def test_path_versions():
    client = Client(
        "https://endeavor.example.com",
        client_id="client-id",
        client_secret="client-secret",
    )

    assert str(client._make_endpoint("agents")) == (
        "https://endeavor.example.com/v2/agents"
    )
    assert str(client._make_auth_endpoint("authenticate")) == (
        "https://endeavor.example.com/v1/authenticate"
    )
    assert (
        str(client._make_execution_endpoint("support-bot", "summarize"))
        == "https://endeavor.example.com/api/support-bot/summarize"
    )
    assert (
        str(
            client._make_execution_endpoint(
                "support-bot",
                "summarize",
                environment="staging",
                version="1.2.3",
            )
        )
        == "https://endeavor.example.com/api/staging/support-bot/summarize/1.2.3"
    )


def test_patch_sends_json(httpserver):
    httpserver.expect_request(
        "/v2/agents/support-bot",
        method="PATCH",
        json={"description": "Updated description"},
    ).respond_with_json(
        {
            "id": "01J7ABC",
            "name": "Support Bot",
            "description": "Updated description",
        }
    )

    client = Client(httpserver.url_for(""))
    result = client.patch(
        {"description": "Updated description"},
        "agents",
        "support-bot",
        require_authentication=False,
    )

    assert result["description"] == "Updated description"


def test_extra_headers_do_not_mutate_defaults(httpserver):
    """
    The _request method accepts extra headers. This test ensures
    that these extra headers do not mutate the default headers.
    """
    httpserver.expect_request(
        "/v2/agents",
        method="GET",
        headers={"X-Request-ID": "request-123"},
    ).respond_with_json([])

    client = Client(httpserver.url_for(""))
    original_headers = dict(client._headers)

    client.get(
        "agents",
        require_authentication=False,
        extra_headers={"X-Request-ID": "request-123"},
    )

    assert client._headers == original_headers
    assert "X-Request-ID" not in client._headers


def test_multipart_request(httpserver, tmp_path):
    def check_request(request):
        assert request.content_type.startswith("multipart/form-data")
        assert "file" in request.files
        assert request.files["file"].filename == "example.txt"

        return WerkzeugResponse(
            json.dumps({"uploaded": True}),
            status=200,
            content_type="application/json",
        )

    httpserver.expect_request(
        "/v2/media",
        method="POST",
    ).respond_with_handler(check_request)

    file_path = tmp_path / "example.txt"
    file_path.write_text("example content")

    client = Client(httpserver.url_for(""))
    with file_path.open("rb") as file_handle:
        result = client.post(
            {"description": "Example file"},
            "media",
            require_authentication=False,
            files={
                "file": (
                    "example.txt",
                    file_handle,
                    "text/plain",
                )
            },
        )

    assert result["uploaded"] is True


def test_streaming_response(httpserver):
    httpserver.expect_request(
        "/v2/media/download",
        method="GET",
    ).respond_with_data(
        b"first chunk\nsecond chunk\n",
        content_type="application/octet-stream",
    )

    client = Client(httpserver.url_for(""))
    response = client.get(
        "media",
        "download",
        require_authentication=False,
        stream=True,
    )

    assert isinstance(response, RequestsResponse)
    try:
        content = b"".join(response.iter_content(chunk_size=8))
        assert content == b"first chunk\nsecond chunk\n"
    finally:
        response.close()


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({}, "/api/agent/task"),
        ({"version": "1.2.3"}, "/api/agent/task/1.2.3"),
        ({"environment": "staging"}, "/api/staging/agent/task"),
        (
            {"environment": "staging", "version": "1.2.3"},
            "/api/staging/agent/task/1.2.3",
        ),
    ],
)
def test_execution_endpoint(kwargs, expected):
    client = Client("https://endeavor.example.com")

    assert str(client._make_execution_endpoint("agent", "task", **kwargs)) == (
        f"https://endeavor.example.com{expected}"
    )


def test_execution_endpoint_accepts_full_url_with_same_hostname():
    client = Client("https://endeavor.example.com")
    deployed_task_url = "https://endeavor.example.com/api/agent/task"

    endpoint = client._make_execution_endpoint(
        deployed_task_url=deployed_task_url,
    )

    assert str(endpoint) == deployed_task_url


@pytest.mark.parametrize(
    "deployed_task_url",
    [
        "/api/agent/task",
        "agent/task",
        "ftp://endeavor.example.com/api/agent/task",
        "https:///api/agent/task",
    ],
)
def test_execution_endpoint_rejects_relative_or_invalid_full_url(
    deployed_task_url,
):
    client = Client("https://endeavor.example.com")

    with pytest.raises(
        ValueError,
        match=r"absolute HTTP\(S\) URL",
    ):
        client._make_execution_endpoint(
            deployed_task_url=deployed_task_url,
        )


def test_execution_endpoint_warns_when_full_url_ignores_path_arguments():
    client = Client("https://endeavor.example.com")
    deployed_task_url = "https://endeavor.example.com/api/full-url/task"

    with pytest.warns(
        UserWarning,
        match=(
            "agent, task, environment, version will be ignored because "
            "deployed_task_url was provided"
        ),
    ):
        endpoint = client._make_execution_endpoint(
            "ignored-agent",
            "ignored-task",
            deployed_task_url=deployed_task_url,
            environment="ignored-environment",
            version="1.2.3",
        )

    assert str(endpoint) == deployed_task_url


def test_execution_endpoint_rejects_full_url_with_different_hostname():
    client = Client("https://endeavor.example.com")

    with pytest.raises(
        ValueError,
        match="must use the configured Endeavor origin",
    ):
        client._make_execution_endpoint(
            deployed_task_url="https://other.example.com/api/agent/task",
        )


def test_execution_endpoint_rejects_full_url_with_different_scheme():
    client = Client("https://endeavor.example.com")

    with pytest.raises(
        ValueError,
        match="must use the configured Endeavor origin",
    ):
        client._make_execution_endpoint(
            deployed_task_url="http://endeavor.example.com/api/agent/task",
        )


def test_execution_endpoint_rejects_full_url_with_different_port():
    client = Client("https://endeavor.example.com")

    with pytest.raises(
        ValueError,
        match="must use the configured Endeavor origin",
    ):
        client._make_execution_endpoint(
            deployed_task_url=("https://endeavor.example.com:8443/api/agent/task"),
        )


def test_execution_endpoint_treats_default_https_port_as_443():
    client = Client("https://endeavor.example.com")
    deployed_task_url = "https://endeavor.example.com:443/api/agent/task"

    endpoint = client._make_execution_endpoint(
        deployed_task_url=deployed_task_url,
    )

    assert str(endpoint) == deployed_task_url


def test_execution_endpoint_rejects_full_url_with_user_information():
    client = Client("https://endeavor.example.com")

    with pytest.raises(
        ValueError,
        match="must not contain user information",
    ):
        client._make_execution_endpoint(
            deployed_task_url=(
                "https://user:password@endeavor.example.com/api/agent/task"
            ),
        )


def test_execution_endpoint_requires_explicit_cross_origin_option():
    client = Client("https://endeavor.example.com")
    deployed_task_url = "https://other.example.com/api/agent/task"

    with pytest.raises(
        ValueError,
        match="must use the configured Endeavor origin",
    ):
        client._make_execution_endpoint(
            deployed_task_url=deployed_task_url,
        )

    endpoint = client._make_execution_endpoint(
        deployed_task_url=deployed_task_url,
        allow_cross_origin=True,
    )

    assert str(endpoint) == deployed_task_url


def test_execution_endpoint_requires_url():
    client = Client("https://endeavor.example.com")
    client.url = None

    with pytest.raises(
        ClientError,
        match="no Endeavor URL has been configured",
    ):
        client.execute("agent", "task")


@pytest.mark.parametrize(
    "agent,task",
    [
        ("agent-slug", "01J7ABCDEF0123456789ABCDE"),
        ("01J7ABCDEF0123456789ABCDE", "task-slug"),
    ],
)
def test_execution_endpoint_accepts_independent_slug_and_ulid_forms(agent, task):
    client = Client("https://endeavor.example.com")

    endpoint = client._make_execution_endpoint(agent, task)

    assert endpoint.path.endswith(f"/api/{agent}/{task}")


@pytest.mark.parametrize(
    "value",
    [
        "",
        ".",
        "..",
        " agent",
        "agent ",
        "agent/task",
        r"agent\task",
        "agent?x",
        "agent#fragment",
        "%2Fv2%2Fagents",
        "agent%2Ftask",
    ],
)
def test_execution_endpoint_rejects_unsafe_components(value):
    client = Client("https://endeavor.example.com")

    with pytest.raises(ValueError):
        client._make_execution_endpoint(value, "task")


@pytest.mark.parametrize(
    "value",
    [
        "support-bot",
        "staging",
        "01J7ABCDEF0123456789ABCDE",
    ],
)
def test_execution_endpoint_accepts_safe_components(value):
    client = Client("https://endeavor.example.com")

    endpoint = client._make_execution_endpoint(value, "task")

    assert endpoint.path == f"/api/{value}/task"


@pytest.mark.parametrize(
    "value",
    [
        "1",
        "1.2",
        "v1.2.3",
        "1.2.3/extra",
        "1.0.0-01",
        "1.0.0-alpha.01",
    ],
)
def test_execution_endpoint_rejects_invalid_versions(value):
    client = Client("https://endeavor.example.com")

    with pytest.raises(ValueError):
        client._make_execution_endpoint("agent", "task", version=value)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, "{}"),
        ("hello", '"hello"'),
        ({"question": "hello"}, '{"question": "hello"}'),
    ],
)
def test_serialize_context(value, expected):
    assert _serialize_context(value) == expected


def test_execute_posts_json_to_path(httpserver):
    httpserver.expect_request(
        "/api/staging/agent/task/1.2.3",
        method="POST",
        json={"question": "hello"},
    ).respond_with_json({"answer": 42})

    client = Client(httpserver.url_for(""))
    client._pre_flight = lambda require_authentication=True: dict(client._headers)

    result = client.execute(
        "agent",
        "task",
        {"question": "hello"},
        environment="staging",
        version="1.2.3",
    )

    assert result == {"answer": 42}


def test_execute_accepts_file_shorthand(httpserver, tmp_path):
    def check_request(request):
        assert request.files["example.pdf"].filename == "example.pdf"
        assert request.files["example.pdf"].read() == b"pdf bytes"
        return WerkzeugResponse("ok", status=200, content_type="text/plain")

    httpserver.expect_request(
        "/api/agent/task",
        method="POST",
    ).respond_with_handler(check_request)

    path = tmp_path / "example.pdf"
    path.write_bytes(b"pdf bytes")
    client = Client(httpserver.url_for(""))
    client._pre_flight = lambda require_authentication=True: dict(client._headers)

    with path.open("rb") as handle:
        result = client.execute(
            "agent",
            "task",
            files={"example.pdf": handle},
        )

    assert result == b"ok"


def test_execute_normalizes_empty_files_to_json_request(httpserver):
    def check_request(request):
        assert request.content_type == "application/json"
        assert request.get_json() == {"question": "hello"}
        assert not request.files
        return WerkzeugResponse("ok", status=200, content_type="text/plain")

    httpserver.expect_request(
        "/api/agent/task",
        method="POST",
    ).respond_with_handler(check_request)

    client = Client(httpserver.url_for(""))
    client._pre_flight = lambda require_authentication=True: dict(client._headers)

    result = client.execute(
        "agent",
        "task",
        context={"question": "hello"},
        files={},
    )

    assert result == b"ok"


def test_execute_serializes_none_context_for_multipart(httpserver):
    def check_request(request):
        assert request.content_type.startswith("multipart/form-data")
        assert json.loads(request.form["context"]) == {}
        return WerkzeugResponse("ok", status=200, content_type="text/plain")

    httpserver.expect_request(
        "/api/agent/task",
        method="POST",
    ).respond_with_handler(check_request)

    client = Client(httpserver.url_for(""))
    client._pre_flight = lambda require_authentication=True: dict(client._headers)

    result = client.execute(
        "agent",
        "task",
        context=None,
        files={"document": io.BytesIO(b"document bytes")},
    )

    assert result == b"ok"


def test_handle_raw_returns_success_response(httpserver):
    httpserver.expect_request("/api/agent/task", method="POST").respond_with_data(
        "hello",
        content_type="text/plain; charset=utf-8",
    )

    client = Client(httpserver.url_for(""))
    client._pre_flight = lambda require_authentication=True: dict(client._headers)
    result = client.execute("agent", "task", raw=True)

    assert isinstance(result, RequestsResponse)
    assert result.headers["Content-Type"].startswith("text/plain")
    assert result.text == "hello"
    result.close()


@pytest.mark.parametrize(
    "status,exception",
    [
        (400, ClientError),
        (404, NotFound),
        (500, ServerError),
    ],
)
def test_execute_uses_standard_error_handling(httpserver, status, exception):
    httpserver.expect_request("/api/agent/task", method="POST").respond_with_data(
        '{"error":"failed"}',
        status=status,
        content_type="application/json",
    )

    client = Client(httpserver.url_for(""))
    client._pre_flight = lambda require_authentication=True: dict(client._headers)

    with pytest.raises(exception):
        client.execute("agent", "task")


def response(
    status: int,
    body: bytes,
    *,
    reason: str = "",
    content_type: str = "application/json",
) -> RequestsResponse:
    rep = RequestsResponse()
    rep.status_code = status
    rep.reason = reason
    rep._content = body
    rep.headers["Content-Type"] = content_type
    return rep


def test_format_response_error_reads_json_error():
    rep = response(
        400,
        b'{"error":"task context must be valid JSON"}',
        reason="Bad Request",
    )

    assert _format_response_error(rep) == (
        "HTTP 400 Bad Request: task context must be valid JSON"
    )


def test_format_response_error_reads_plain_text():
    rep = response(
        502,
        b"upstream unavailable",
        reason="Bad Gateway",
        content_type="text/plain",
    )

    assert _format_response_error(rep) == ("HTTP 502 Bad Gateway: upstream unavailable")


def test_format_response_error_reads_field_errors():
    rep = response(
        422,
        (
            b'{"error":"validation failed","errors":['
            b'{"field":"name","error":"is required"},'
            b'{"field":"version","error":"is invalid"}]}'
        ),
        reason="Unprocessable Entity",
    )

    assert _format_response_error(rep) == (
        "HTTP 422 Unprocessable Entity: validation failed; "
        "name: is required; version: is invalid"
    )


@pytest.mark.parametrize(
    "status,exception",
    [
        (401, AuthenticationError),
        (403, AuthenticationError),
        (500, ServerError),
    ],
)
def test_handle_includes_status_and_detail_in_error(status, exception):
    client = Client("https://endeavor.example.com")
    rep = response(
        status,
        b'{"error":"detailed failure"}',
        reason="Failure",
    )

    with pytest.raises(
        exception,
        match=f"HTTP {status} Failure: detailed failure",
    ):
        client.handle(rep)


def test_execute_uses_configured_timeout(monkeypatch):
    client = Client("https://endeavor.example.com", timeout=7.5)
    client._pre_flight = lambda require_authentication=True: dict(client._headers)
    captured = {}

    def request(method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["timeout"] = kwargs["timeout"]
        response = RequestsResponse()
        response.status_code = 200
        response.headers["Content-Type"] = "application/json"
        response._content = b'{"ok": true}'
        return response

    monkeypatch.setattr(client.session, "request", request)

    assert client.execute("agent", "task") == {"ok": True}
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/api/agent/task")
    assert captured["timeout"] == 7.5
