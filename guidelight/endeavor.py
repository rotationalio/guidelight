"""High-level Endeavor SDK entry point."""

from __future__ import annotations

from .client import Client
from .resources.agents import Agents


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
