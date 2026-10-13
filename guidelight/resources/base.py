"""Shared high-level resource-manager mechanics."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Generic, Iterable, TypeVar

from pydantic import ValidationError

from ..client import Client
from ..models.base import RequestModel

T = TypeVar("T")
ULID_RE = re.compile(r"^[0-7][0-9ABCDEFGHJKMNPQRSTVWXYZ]{25}$", re.IGNORECASE)


@dataclass(frozen=True)
class PageInfo:
    """Pagination metadata returned with an Endeavor collection response.

    ``page_size`` is the server's page-size value when provided, and
    ``offset`` is the zero-based starting position for the collection page.
    """

    page_size: int | None = None
    offset: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "PageInfo":
        """Build pagination metadata from an optional response envelope."""
        data = data or {}
        return cls(
            page_size=data.get("page_size"),
            offset=data.get("offset", 0),
        )


@dataclass
class Page(Generic[T]):
    """Typed collection page returned by a resource manager.

    ``items`` contains the decoded resource models, ``page_info`` contains
    pagination metadata, and ``metadata`` preserves additional envelope
    fields returned by Endeavor.
    """

    items: list[T]
    page_info: PageInfo
    metadata: dict[str, Any] = field(default_factory=dict)

    def __iter__(self):
        """Iterate over the decoded resources in the page."""
        return iter(self.items)

    def __len__(self) -> int:
        """Return the number of decoded resources in the page."""
        return len(self.items)


def _safe_reference(value: str) -> str:
    """Validate a single path-safe resource reference component."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("resource reference must be a non-empty string")
    value = value.strip()
    if value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError("resource reference must not contain path separators")
    return value


def reference(value: Any, *, allow_slug: bool = False) -> str:
    """Resolve a resource model, ULID, or permitted slug to a path reference."""
    if isinstance(value, str):
        value = _safe_reference(value)
        if not allow_slug and not ULID_RE.fullmatch(value):
            raise ValueError("resource reference must be a valid ULID")
        return value

    slug = getattr(value, "slug", None)
    identifier = getattr(value, "id", None)
    if identifier:
        value = _safe_reference(str(identifier))
        if not allow_slug and not ULID_RE.fullmatch(value):
            raise ValueError("resource reference must be a valid ULID")
        return value
    if allow_slug and slug:
        return _safe_reference(slug)
    raise ValueError("resource must provide an id or supported slug")


def resolve_resource_ref(value: Any) -> str:
    """Resolve a resource reference, permitting IDs and resource slugs.

    This convenience function calls ``reference`` with ``allow_slug=True``.
    """
    return reference(value, allow_slug=True)


def request_object(
    request_type: type[RequestModel],
    request: RequestModel | None,
    fields: dict[str, Any],
) -> RequestModel:
    """Validate a request model or construct one from keyword fields."""
    if request is not None and fields:
        raise TypeError("provide either a request object or keyword fields")
    if request is not None and not isinstance(request, request_type):
        raise TypeError(f"expected {request_type.__name__}")
    if request is None:
        try:
            return request_type.model_validate(fields)
        except ValidationError as exc:
            raise TypeError(f"invalid {request_type.__name__} fields") from exc
    return request


def decode_page(
    body: object,
    *,
    key: str,
    model: type[T],
) -> Page[T]:
    """Decode a standard Endeavor collection envelope into a typed page."""
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
        raise TypeError(f"expected a list or dict response, got {type(body).__name__}")

    return Page(
        items=[model.model_validate(item) for item in values],
        page_info=page_info,
        metadata=metadata,
    )


def decode_many(
    body: object,
    *,
    key: str,
    model: type[T],
) -> list[T]:
    """Decode a list response and reject malformed envelopes or entries."""
    if isinstance(body, list):
        values = body
    elif isinstance(body, dict):
        values = body.get(key)
    else:
        raise TypeError(f"expected a list or dict response, got {type(body).__name__}")

    if not isinstance(values, list):
        raise TypeError(f"expected {key!r} to contain a list")
    if not all(isinstance(item, dict) for item in values):
        raise TypeError(f"expected every {key!r} item to be an object")

    return [model.model_validate(item) for item in values]


class ResourceManager:
    """Base behavior shared by explicit high-level resource managers."""

    collection_path: tuple[str, ...] = ()
    valid_filters: frozenset[str] = frozenset()

    def __init__(self, client: Client):
        """Create a manager backed by an authenticated low-level client."""
        self._client = client

    @property
    def client(self) -> Client:
        """Return the low-level client used for manager requests."""
        return self._client

    def _path(self, *parts: str) -> tuple[str, ...]:
        """Append validated resource path components to the collection path."""
        return self.collection_path + parts

    def _query(
        self,
        *,
        page_size: int | None = None,
        offset: int = 0,
        order_by: str | Iterable[str] | None = None,
        filters: dict[str, Any] | None = None,
        **extra_filters: Any,
    ) -> dict[str, Any]:
        """Build a query and reject filters unsupported by this manager."""
        combined_filters = dict(filters or {})
        combined_filters.update(extra_filters)
        unknown = set(combined_filters) - self.valid_filters
        if unknown:
            names = ", ".join(sorted(unknown))
            raise TypeError(f"unsupported filter(s): {names}")
        query: dict[str, Any] = {"offset": offset}
        if page_size is not None:
            query["page_size"] = page_size
        if order_by is not None:
            query["order_by"] = order_by
        query.update(
            {key: value for key, value in combined_filters.items() if value is not None}
        )
        return query

    def iterate(self, **options: Any):
        """Yield resources from successive offset-based collection pages."""
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
