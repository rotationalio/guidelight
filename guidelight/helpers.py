import json
import re

from json import JSONDecodeError
from typing import Any
from urllib.parse import urlsplit

from requests import Response

from .url import URL

SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)

PATH_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~+-]*$")


def _validate_path_component(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if value in {".", ".."} or PATH_COMPONENT.fullmatch(value) is None:
        raise ValueError(f"{name} must be a single URL path component")
    return value


def _validate_semver(value: str) -> str:
    value = _validate_path_component(value, "version")
    if SEMVER.fullmatch(value) is None:
        raise ValueError(f"version must be a valid semantic version: {value}")
    return value


def _serialize_context(context: Any) -> str:
    return json.dumps({} if context is None else context)


def _format_response_error(rep: Response) -> str:
    message = f"HTTP {rep.status_code}"

    if rep.reason:
        message += f" {rep.reason}"

    details: list[str] = []

    try:
        body = rep.json()
    except JSONDecodeError:
        text = rep.text.strip()
        if text:
            details.append(text[:1000])
    else:
        if isinstance(body, dict):
            error = body.get("error") or body.get("message")
            if error:
                details.append(str(error))

            errors = body.get("errors")
            if isinstance(errors, list):
                for item in errors:
                    if not isinstance(item, dict):
                        continue

                    field = item.get("field")
                    error = item.get("error")

                    if field and error:
                        details.append(f"{field}: {error}")
                    elif error:
                        details.append(str(error))

        elif body is not None:
            details.append(str(body))

    if details:
        message += ": " + "; ".join(details)

    return message


def _url_origin(value: str | URL) -> tuple[str, str, int]:
    parsed = urlsplit(str(value))
    if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
        raise ValueError("URL must be an absolute HTTP(S) URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL must not contain user information")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("URL contains an invalid port") from exc
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return (
        parsed.scheme.lower(),
        parsed.hostname.lower().rstrip("."),
        port,
    )
