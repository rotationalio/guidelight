import json

from pytest_httpserver import HTTPServer
from requests import Response as RequestsResponse
from werkzeug.wrappers import Response as WerkzeugResponse

from guidelight.client import Client

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

    # Start a guidelight client
    client = Client(
        "http://localhost:%d" % server.port, client_id="id", client_secret="secret"
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
    assert str(
        client._make_execution_endpoint("support-bot", "summarize")
    ) == "https://endeavor.example.com/api/support-bot/summarize"


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