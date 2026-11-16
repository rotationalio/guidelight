"""
Exception class hierarchy for guidelight related exceptions.
"""


class GuidelightError(Exception):
    """
    Base class for all guidelight related exceptions.
    """


class EndeavorError(GuidelightError):
    """
    Base class for all endeavor related exceptions.
    """


class ServerError(EndeavorError):
    """
    An error that is raised when the server returns a 500 status code.
    """


class ClientError(EndeavorError):
    """
    An unspecified client side error when the server returns a 400 status code.
    """


class AuthenticationError(ClientError):
    """
    Occurs when the server returns a 401 or 403 error code.
    """


class NotFound(ClientError):
    """
    Occurs when the server returns a 404 error code.
    """


class ValidationError(ClientError):
    """
    The payload is invalid or a preflight check has failed.
    """


class ReadOnlyEndpoint(EndeavorError):
    """
    The associated resource does not allow create, update, or delete methods
    """


class UnsupportedResponseType(EndeavorError):
    """The task returned a successful but unsupported media type."""

    def __init__(self, mime_type: str):
        self.mime_type = mime_type
        super().__init__(
            f"unsupported task response content type: {mime_type or '<missing>'}"
        )


class InvalidResponse(EndeavorError):
    """The server returned a successful response with an invalid body."""


class IntegrationAuthorizationRequired(UserWarning):
    """An Integration requires browser-based authorization."""

    def __init__(self, integration_id: str | None, integration_url: str):
        self.integration_id = integration_id
        self.integration_url = integration_url
        super().__init__(
            "Integration authorization is required. "
            f"Open {self.integration_url} in Endeavor to authorize it."
        )


class IntegrationRegistrationRequired(UserWarning):
    """An Integration requires OAuth application registration."""

    def __init__(self, integration_id: str | None, integration_url: str):
        self.integration_id = integration_id
        self.integration_url = integration_url
        super().__init__(
            "Integration OAuth application registration is required. "
            f"Open {self.integration_url} in Endeavor to configure it."
        )


class IntegrationStatusError(EndeavorError):
    """An Integration reached a terminal failure status."""

    def __init__(self, integration_id: str, status: str):
        self.integration_id = integration_id
        self.status = status
        super().__init__(
            f"Integration {integration_id} reached terminal status {status!r}."
        )


class IntegrationStatusTimeout(EndeavorError):
    """An Integration did not reach a terminal status before the timeout."""

    def __init__(self, integration_id: str, status: str, timeout: float):
        self.integration_id = integration_id
        self.status = status
        self.timeout = timeout
        super().__init__(
            f"Integration {integration_id} remained in status {status!r} "
            f"after {timeout:g} seconds."
        )


class IntegrationPendingWarning(UserWarning):
    """An Integration was created while asynchronous discovery is pending."""
