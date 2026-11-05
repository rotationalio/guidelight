from guidelight.models import Media


def test_media_decodes_metadata_and_modality():
    media = Media.from_dict(
        {
            "id": "01JMEDIA",
            "name": "generated.png",
            "content_type": "image/png",
            "modality": ["Image"],
            "file_size": 123,
            "checksum": "abc",
            "created_by": "01JCREATOR",
            "converted_from": "01JSOURCE",
            "download_url": "https://example.test/v2/media/01J/download/generated.png",
        }
    )

    assert media.name == "generated.png"
    assert media.content_type == "image/png"
    assert media.modality == ["Image"]
    assert media.created_by == "01JCREATOR"
    assert media.converted_from == "01JSOURCE"
    assert media.download_url.startswith("https://")
