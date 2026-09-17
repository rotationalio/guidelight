"""Shared high-level resource-manager mechanics."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Generic, Iterable, TypeVar

from ..client import Client

T = TypeVar("T")
ULID_RE = re.compile(r"^[0-7][0-9ABCDEFGHJKMNPQRSTVWXYZ]{25}$", re.IGNORECASE)


@dataclass(frozen=True)
class PageInfo:
    """Offset-based pagination metadata returned by Endeavor."""

    page_size: int | None = None
    offset: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "PageInfo":
        data = data or {}
        return cls(
            page_size=data.get("page_size"),
            offset=data.get("offset", 0),
        )


@dataclass
class Page(Generic[T]):
    """A page of typed resources plus response metadata."""

    items: list[T]
    page: PageInfo
    metadata: dict[str, Any] = field(default_factory=dict)

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


def _safe_reference(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("resource reference must be a non-empty string")
    value = value.strip()
    if value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError("resource reference must not contain path separators")
    return value


def reference(value: Any, *, allow_slug: bool = False) -> str:
    """Resolve a model or string into a safe API path reference."""
    if isinstance(value, str):
        value = _safe_reference(value)
        if not allow_slug and not ULID_RE.fullmatch(value):
            raise ValueError("resource reference must be a valid ULID")
        return value

    slug = getattr(value, "slug", None)
    identifier = getattr(value, "id", None)
    if allow_slug and slug:
        return _safe_reference(slug)
    if identifier:
        value = _safe_reference(str(identifier))
        if not allow_slug and not ULID_RE.fullmatch(value):
            raise ValueError("resource reference must be a valid ULID")
        return value
    raise ValueError("resource must provide an id or supported slug")


def decode_page(
    body: dict[str, Any] | list[Any],
    *,
    key: str,
    model: type[T],
) -> Page[T]:
    """Decode a standard Endeavor list response."""
    if isinstance(body, list):
        values = body
        metadata: dict[str, Any] = {}
        page_info = PageInfo()
    elif isinstance(body, dict):
        values = body.get(key, [])
        page_info = PageInfo.from_dict(body.get("page"))
        metadata = {
            name: value for name, value in body.items() if name not in {key, "page"}
        }
    else:
        raise TypeError(f"expected a list response, got {type(body).__name__}")

    return Page(
        items=[model.from_dict(item) for item in values],
        page=page_info,
        metadata=metadata,
    )


class ResourceManager:
    """Base class for explicit resource managers."""

    collection_path: tuple[str, ...] = ()
    valid_filters: frozenset[str] = frozenset()

    def __init__(self, client: Client):
        self._client = client

    @property
    def client(self) -> Client:
        return self._client

    def _path(self, *parts: str) -> tuple[str, ...]:
        return self.collection_path + parts

    def _query(
        self,
        *,
        page_size: int | None = None,
        offset: int = 0,
        order_by: str | Iterable[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        filters = filters or {}
        unknown = set(filters) - self.valid_filters
        if unknown:
            names = ", ".join(sorted(unknown))
            raise TypeError(f"unsupported filter(s): {names}")

        query: dict[str, Any] = {"offset": offset}
        if page_size is not None:
            query["page_size"] = page_size
        if order_by is not None:
            query["order_by"] = order_by
        query.update({key: value for key, value in filters.items() if value is not None})
        return query

    def iterate(self, **options: Any):
        """Yield all items using offset-based pages."""
        page_size = options.get("page_size")
        offset = options.get("offset", 0)
        while True:
            page = self.list(**{**options, "offset": offset})
            yield from page.items
            if not page.items or (
                page_size is not None and len(page.items) < page_size
            ):
                return
            offset += len(page.items)
