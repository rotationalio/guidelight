from io import BytesIO

import pytest
from requests import Response

from guidelight.client import Client
from guidelight.resources.media import MediaCollection

MEDIA_ID = "01ARZ3NDEKTSV4RRFFQ69G5FBA"


def _media_body(media_id=MEDIA_ID):
    return {
        "id": media_id,
        "name": "example.png",
        "content_type": "image/png",
        "modality": ["Image"],
        "file_size": 12,
    }


def test_media_manager_lists_updates_and_deletes_media(client):
    client.responses.extend(
        [
            {"page": {}, "media": [_media_body()]},
            _media_body(),
        ]
    )
    media = MediaCollection(client)

    page = media.list(content_type="image/png")
    updated = media.update(MEDIA_ID, name="renamed.png")
    media.delete(MEDIA_ID)

    assert page.items[0].name == "example.png"
    assert updated.name == "example.png"
    assert client.calls == [
        ("GET", ("media",), {"offset": 0, "content_type": "image/png"}),
        ("PATCH", ("media", MEDIA_ID), {"name": "renamed.png"}, {}),
        ("DELETE", ("media", MEDIA_ID), {}),
    ]


def test_media_search_supports_unknown_filter(client):
    client.responses.append({"page": {}, "media": [_media_body()]})

    page = MediaCollection(client).search(
        "example",
        content_type="image/png",
        unknown=True,
    )

    assert page.items[0].id == MEDIA_ID
    assert client.calls == [
        (
            "GET",
            ("media", "search"),
            {
                "offset": 0,
                "content_type": "image/png",
                "unknown": True,
                "query": "example",
            },
        )
    ]


def test_media_list_rejects_search_only_unknown_filter(client):
    with pytest.raises(TypeError, match="unsupported filter.*unknown"):
        MediaCollection(client).list(unknown=True)


def test_media_download_streams_response(client):
    response = Response()
    response.status_code = 200
    response.headers["Content-Type"] = "image/png"
    response.headers["Content-Length"] = "11"
    response._content = b"image bytes"
    response._content_consumed = True
    client.responses.append(response)

    destination = BytesIO()
    with MediaCollection(client).download(MEDIA_ID, filename="example.png") as download:
        assert download.content_type == "image/png"
        assert download.content_length == 11
        assert download.write_to(destination, chunk_size=4) == 11

    assert destination.getvalue() == b"image bytes"
    assert client.calls == [
        (
            "GET",
            ("media", MEDIA_ID, "download", "example.png"),
            None,
            {
                "stream": True,
                "raw": True,
            },
        )
    ]


@pytest.mark.parametrize(
    "filename",
    [
        "",
        " ",
        ".",
        "..",
        "/etc/passwd",
        "../secret.txt",
        "folder/secret.txt",
        r"folder\secret.txt",
        "%2Fv2%2Fagents",
        "image.png?download=false",
        "image.png#fragment",
    ],
)
def test_media_download_rejects_unsafe_filename(client, filename):
    with pytest.raises(
        ValueError,
        match="filename must be a single URL path component|non-empty string",
    ):
        MediaCollection(client).download(MEDIA_ID, filename=filename)

    assert client.calls == []


def test_media_download_context_closes_http_response(httpserver):
    httpserver.expect_request(
        f"/v2/media/{MEDIA_ID}/download/example.png",
        method="GET",
        headers={"Authorization": "Bearer test-token"},
    ).respond_with_data(
        b"image bytes",
        content_type="image/png",
    )
    client = Client(httpserver.url_for(""))

    def preflight(require_authentication=True):
        assert require_authentication is True
        return {"Authorization": "Bearer test-token"}

    client._pre_flight = preflight

    with MediaCollection(client).download(
        MEDIA_ID,
        filename="example.png",
    ) as download:
        response = download.response
        assert response.raw is not None
        assert not response.raw.closed

    assert response.raw.closed
