from datetime import datetime

from pydantic import Field

from .base import ModalityName, RequestModel, ResponseModel


class Media(ResponseModel):
    id: str | None = None
    name: str = ""
    description: str = ""
    content_type: str = ""
    modality: list[ModalityName] = Field(default_factory=list)
    file_size: int | None = None
    checksum: str = ""
    created_by: str | None = None
    converted_from: str | None = None
    download_url: str | None = None
    created: datetime | None = None
    modified: datetime | None = None


class MediaUpdate(RequestModel):
    """Mutable Media metadata accepted by PATCH."""

    name: str | None = None
    description: str | None = None
    content_type: str | None = None
