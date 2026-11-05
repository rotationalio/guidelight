"""Media resource manager."""

from __future__ import annotations

from typing import Any

from ..helpers import _validate_path_component
from ..media import MediaDownload
from ..models import Media, MediaUpdate
from .base import CollectionManager, Page, decode_page, reference, request_object


class MediaCollection(CollectionManager[Media]):
    """Manage Media metadata and authenticated downloads."""

    # NOTE: Named this to MediaCollection to avoid confusion with the Media model

    collection_path = ("media",)
    valid_filters = frozenset({"content_type", "modality", "created_by"})

    def list(
        self,
        *,
        page_size: int | None = None,
        offset: int = 0,
        order_by: str | list[str] | None = None,
        **filters: Any,
    ) -> Page[Media]:
        """List Media metadata."""
        query = self._query(
            page_size=page_size,
            offset=offset,
            order_by=order_by,
            filters=filters,
        )
        body = self.client.get(*self.collection_path, query=query)
        return decode_page(body, key="media", model=Media)

    def __iter__(self):
        """Iterate over Media metadata."""
        return self.iterate()

    def search(self, query: str, **options: Any) -> Page[Media]:
        """Search Media by server-supported metadata fields.

        Args:
            query: Text to search for in Media metadata.
            **options: Pagination options and ``content_type``, ``modality``,
                or ``created_by`` filters. Set ``unknown=True`` to restrict
                results to Media whose content type Endeavor records as
                unknown. Omitting ``unknown`` or setting it to ``False`` does
                not apply that restriction.
        """
        unknown = options.pop("unknown", None)
        filters = {
            key: options.pop(key) for key in list(options) if key in self.valid_filters
        }
        params = self._query(filters=filters, **options)
        if unknown is not None:
            params["unknown"] = unknown
        params["query"] = query
        body = self.client.get("media", "search", query=params)
        return decode_page(body, key="media", model=Media)

    def update(self, ref: Any, request=None, **fields: Any) -> Media:
        """Patch mutable Media metadata.

        Endeavor preserves omitted ``description`` and ``content_type`` fields.
        An omitted ``name`` follows Endeavor's filename normalization and may
        become ``<media-id>.bin``; supply ``name`` to preserve a non-default
        filename. Empty description and content type values are treated as
        omitted and do not clear existing values.
        """
        request = request_object(MediaUpdate, request, fields)
        body = self.client.patch(
            request.to_dict(),
            "media",
            reference(ref),
        )
        return Media.from_dict(body)

    def delete(self, ref: Any) -> None:
        """Delete Media metadata and its unreferenced blob."""
        self.client.delete("media", reference(ref))

    def download(
        self,
        ref: Any,
        *,
        filename: str = "download",
    ) -> MediaDownload:
        """Stream a Media file using one path-safe filename component."""
        filename = _validate_path_component(filename, "filename")
        response = self.client.get(
            "media",
            reference(ref),
            "download",
            filename,
            stream=True,
            raw=True,
        )
        return MediaDownload(response)
