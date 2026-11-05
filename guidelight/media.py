"""Streaming Media download helpers."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from requests import Response

DEFAULT_CHUNK_SIZE = 1024 * 1024


class MediaDownload:
    """A closable streamed Media response."""

    def __init__(self, response: Response) -> None:
        self.response = response

    @property
    def content_type(self) -> str:
        """Return the response content type."""
        return self.response.headers.get("Content-Type", "")

    @property
    def content_length(self) -> int | None:
        """Return the declared content length, when available."""
        value = self.response.headers.get("Content-Length")
        return int(value) if value and value.isdigit() else None

    def write_to(
        self,
        destination: str | Path | BinaryIO,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> int:
        """Stream the response into a path or writable binary file."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        if isinstance(destination, (str, Path)):
            with Path(destination).open("wb") as output:
                return self._write_to_stream(output, chunk_size)

        return self._write_to_stream(destination, chunk_size)

    def _write_to_stream(self, output: BinaryIO, chunk_size: int) -> int:
        """Write response chunks to an already-open binary stream."""
        written = 0
        for chunk in self.response.iter_content(chunk_size=chunk_size):
            if chunk:
                output.write(chunk)
                written += len(chunk)
        return written

    def close(self) -> None:
        """Close the underlying HTTP response."""
        self.response.close()

    def __enter__(self) -> MediaDownload:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
