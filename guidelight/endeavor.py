"""High-level Endeavor SDK entry point."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .client import Client
from .exceptions import UnsupportedResponseType
from .resources.agents import Agents
from .url import URL, parse_content_type


class Endeavor:
    """High-level wrapper over an authenticated low-level Client."""

    def __init__(self, client: Client):
        self._client = client
        self.agents = Agents(client)

    @property
    def client(self) -> Client:
        """Return the underlying transport for unsupported or advanced routes."""
        return self._client

    def status(self):
        """Return server status information."""
        return self._client.status()

    def run(
        self,
        agent: str | None = None,
        task: str | None = None,
        context: Any = None,
        *,
        deployed_task_url: str | URL | None = None,
        environment: str | None = None,
        version: str | None = None,
        files: Mapping[str, Any] | None = None,
    ) -> Any:
        response = self._client.execute(
            agent=agent,
            task=task,
            deployed_task_url=deployed_task_url,
            context=context,
            environment=environment,
            version=version,
            files=files,
            raw=True,
        )
        return self._decode_execution_response(response)

    @staticmethod
    def _decode_execution_response(response):
        if response is None:
            return None

        mime, _ = parse_content_type(response.headers.get("Content-Type", ""))
        if mime == "text/plain":
            return response.text
        if mime == "application/json":
            return response.json()
        raise UnsupportedResponseType(mime)
