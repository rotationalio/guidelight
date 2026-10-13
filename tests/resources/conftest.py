"""Pytest fixtures shared by resource-manager tests."""

import pytest

from .shared import FakeClient


@pytest.fixture
def client():
    """Return a fresh fake client for each test."""
    return FakeClient()


@pytest.fixture
def client_factory():
    """Create a fake client with test-specific queued responses."""
    return FakeClient
