"""High-level Endeavor SDK entry point."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .client import Client
from .exceptions import UnsupportedResponseType
from .resources import Agents, Generations, Releases, TestCases
from .url import URL, parse_content_type


class Endeavor:
    """High-level wrapper over an authenticated low-level Client."""

    def __init__(self, client: Client):
        """Initialize the SDK and expose its top-level resource managers.

        ``agents`` is the entry point for Agent resources and Agent-scoped
        Tasks. ``test_cases``, ``generations``, and ``releases`` provide direct
        access to their global collections. Task-scoped Experiments, Metrics,
        Test Cases, and Releases are reached through an Agent's Task manager.
        """
        self._client = client
        self.agents = Agents(client)
        self.test_cases = TestCases(client)
        self.generations = Generations(client)
        self.releases = Releases(client)

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
        """Execute a deployed Task and decode its successful response.

        The Task may be selected with ``agent`` and ``task`` references plus
        optional ``environment`` and ``version`` selectors, or directly with
        ``deployed_task_url``. When ``files`` is provided, the request is sent
        as multipart form data; otherwise the context is sent as JSON.

        Returns:
            The decoded JSON value, plain-text string, or ``None`` for an empty
            successful response.

        Raises:
            UnsupportedResponseType: If the response is neither JSON nor plain
                text.
        """
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
        """Decode a raw successful execution response using its content type.

        JSON responses are returned as decoded Python values, plain-text
        responses are returned as strings, and an absent response is returned
        as ``None``.

        Raises:
            UnsupportedResponseType: If the response content type is not
                supported by the high-level SDK.
        """
        if response is None:
            return None

        mime, _ = parse_content_type(response.headers.get("Content-Type", ""))
        if mime == "text/plain":
            return response.text
        if mime == "application/json":
            return response.json()
        raise UnsupportedResponseType(mime)
