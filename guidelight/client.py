"""
Implements the API client that manages authentication and cookie state of requests to
and from an Endeavor server. These requests integrate guidelight with Endeavor for AI
projects and training.
"""

import os
import logging
import warnings

from typing import Any, Mapping

from requests import Response
from platform import python_version
from requests.sessions import Session
from requests.adapters import HTTPAdapter

from .credentials import Credentials
from .helpers import (
    _format_response_error,
    _serialize_context,
    _validate_path_component,
    _validate_semver,
    _url_origin,
)
from .url import URL, parse_content_type
from .version import get_version
from .exceptions import ClientError, ServerError
from .exceptions import AuthenticationError, NotFound

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


# Setup debug logging for guidelight
logger = logging.getLogger("endeavor")


# Environment variables for local configuration
ENV_URL = "ENDEAVOR_URL"
ENV_CLIENT_ID = "ENDEAVOR_CLIENT_ID"
ENV_CLIENT_SECRET = "ENDEAVOR_CLIENT_SECRET"
ENV_AUTH_URL = "ENDEAVOR_AUTH_URL"

# Default header values
ACCEPT = "application/json"
ACCEPT_LANG = "en-US,en"
ACCEPT_ENCODE = "gzip, deflate, br"


class Client(object):
    """
    Client manages the connection/session to an Endeavor server and makes API requests.

    Parameters
    ----------
    url : str, optional
        The base URL of the Endeavor server. If not provided, defaults to the value of
        the `ENDEAVOR_URL` environment variable. If neither is set, an error is raised.

    client_id : str, optional
        The client ID of your API key for authentication. If not provided, defaults to
        the value of the `ENDEAVOR_CLIENT_ID` environment variable. If neither is set,
        an error is raised.

    client_secret : str, optional
        The client secret of your API key for authentication. If not provided, defaults
        to the value of the `ENDEAVOR_CLIENT_SECRET` environment variable. If neither is
        set, an error is raised.

    auth_url : str, optional
        The base URL of the authentication server (for example,
        ``https://auth.guidelight.dev``). If not provided, defaults to the value of the
        ``ENDEAVOR_AUTH_URL`` environment variable or falls back to the url specified otherwise.

    timeout : float, optional
        The number of seconds to wait for a response until error.

    pool_connections : int, default=8
        The number of urllib3 connections to cache in a pool.

    pool_maxsize : int, default=16
        The maximum number of connections to save in the pool.

    max_retries : int, default=3
        The maximum number of retries for a request. Note, this only applies to failed
        DNS lookups, socket connections and connection timeouts, never to requests where
        data has made it to the server.
    api_version : str, default="v2"
        The version of the API to use.
    auth_version : str, default="v1"
        The version of the authentication API to use.
    """

    def __init__(
        self,
        url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        auth_url: str | None = None,
        timeout: float | None = None,
        pool_connections: int = 8,
        pool_maxsize: int = 16,
        max_retries: int = 3,
        api_version: str = "v2",
        auth_version: str = "v1",
    ) -> None:
        self._host = None
        self._creds = None
        self._prefix = None

        self.url = url or os.environ.get(ENV_URL, "")
        self.client_id = client_id or os.environ.get(ENV_CLIENT_ID, None)
        self.client_secret = client_secret or os.environ.get(ENV_CLIENT_SECRET, None)
        self.auth_url = auth_url or os.environ.get(ENV_AUTH_URL, None)
        self.api_version = api_version
        self.auth_version = auth_version

        user_agent = f"guidelight/{get_version(short=True)} python/{python_version()}"
        self._headers = {
            "Accept": ACCEPT,
            "Accept-Language": ACCEPT_LANG,
            "Accept-Encoding": ACCEPT_ENCODE,
            "User-Agent": user_agent,
        }

        # Configure HTTP requests with the requests library
        self.timeout = timeout
        self.session = Session()
        self.adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=max_retries,
        )
        self.session.mount(self.prefix + "://", self.adapter)

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if value is None:
            self._timeout = (10.0, 30.0)
        else:
            self._timeout = value

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._host = None
        self._prefix = None
        self._url = URL.parse(value) if value else None

    @property
    def auth_url(self):
        if self._auth_url is None:
            return self.url
        return self._auth_url

    @auth_url.setter
    def auth_url(self, value):
        self._auth_url = URL.parse(value) if value else None

    @property
    def host(self):
        if self._host is None and self.url:
            parsed = self.url
            if parsed.netloc:
                self._host = parsed.netloc
            else:
                # if a domain is specified then it will be in the path
                self._host = parsed.path.split("/")[0]

        return self._host

    @property
    def prefix(self):
        if self._prefix is None:
            if not self.host:
                raise ValueError("cannot compute prefix without host")

            if self.is_localhost():
                self._prefix = "http"
            else:
                self._prefix = "https"

        return self._prefix

    def status(self):
        """
        Executes a status request to the Endeavor server to verify connectivity and to
        retrieve server version and uptime information.
        """
        return self.get("status", require_authentication=False)

    def get(
        self,
        *endpoint: str,
        query: dict[str, Any] | None = None,
        require_authentication: bool = True,
        **options: Any,
    ):
        return self._request(
            "GET",
            *endpoint,
            query=query,
            require_authentication=require_authentication,
            **options,
        )

    def post(
        self,
        data,
        *endpoint: str,
        query: dict[str, Any] | None = None,
        require_authentication: bool = True,
        **options: Any,
    ):
        return self._request(
            "POST",
            *endpoint,
            data=data,
            query=query,
            require_authentication=require_authentication,
            **options,
        )

    def put(
        self,
        data,
        *endpoint: str,
        query: dict[str, Any] | None = None,
        require_authentication: bool = True,
        **options: Any,
    ):
        return self._request(
            "PUT",
            *endpoint,
            data=data,
            query=query,
            require_authentication=require_authentication,
            **options,
        )

    def patch(
        self,
        data: dict,
        *endpoint: str,
        query: dict[str, Any] | None = None,
        require_authentication: bool = True,
        **options: Any,
    ):
        return self._request(
            "PATCH",
            *endpoint,
            data=data,
            query=query,
            require_authentication=require_authentication,
            **options,
        )

    def delete(
        self,
        *endpoint: str,
        query: dict[str, Any] | None = None,
        require_authentication: bool = True,
        **options: Any,
    ):
        return self._request(
            "DELETE",
            *endpoint,
            query=query,
            require_authentication=require_authentication,
            **options,
        )

    def execute(
        self,
        agent: str | None = None,
        task: str | None = None,
        context: Any | None = None,
        *,
        deployed_task_url: str | URL | None = None,
        environment: str | None = None,
        version: str | None = None,
        files: Mapping[str, Any] | None = None,
        raw: bool = False,
        allow_cross_origin: bool = False,
    ):
        endpoint = self._make_execution_endpoint(
            agent,
            task,
            deployed_task_url=deployed_task_url,
            environment=environment,
            version=version,
            allow_cross_origin=allow_cross_origin,
        )

        files = files or None

        if files:
            data = {"context": _serialize_context(context)}
        else:
            data = context if context is not None else {}

        return self._request(
            "POST",
            data=data,
            files=files,
            resolved_url=endpoint,
            raw=raw,
        )

    def handle(
        self,
        rep: Response,
        *,
        stream: bool = False,
        raw: bool = False,
    ):
        """
        Handle the response from an API request, raising an error if the request failed.
        """
        if rep.status_code == 401 or rep.status_code == 403:
            raise AuthenticationError(
                f"authentication failed: {_format_response_error(rep)}"
            )

        elif rep.status_code == 204:
            return None

        elif 200 <= rep.status_code < 300:
            if stream or raw:
                return rep

            mimetype, _ = parse_content_type(rep.headers.get("Content-Type"))
            if mimetype == "application/json":
                return rep.json()
            else:
                return rep.content

        elif 400 <= rep.status_code < 500:
            logger.warning(
                "client error: status=%s reason=%s",
                rep.status_code,
                rep.reason or "<missing>",
            )
            message = _format_response_error(rep)

            if rep.status_code == 404:
                raise NotFound(message)
            else:
                raise ClientError(message)

        elif 500 <= rep.status_code < 600:
            logger.warning(
                "server error: status=%s reason=%s",
                rep.status_code,
                rep.reason or "<missing>",
            )

            message = _format_response_error(rep)

            raise ServerError(message)

        else:
            raise ValueError(f"unhandled status code: {_format_response_error(rep)}")

    def is_authenticated(self) -> bool:
        """
        Returns True if there are JWT claims with a valid access token
        """
        return self._creds is not None and self._creds.is_authenticated()

    def is_refreshable(self) -> bool:
        """
        Returns True if there are JWT claims with a valid refresh token
        """
        return self._creds is not None and self._creds.is_refreshable()

    def is_localhost(self) -> bool:
        """
        Returns true if the host is a local domain (e.g. localhost)
        """
        host = self.host
        if ":" in host:
            host = host.split(":")[0]
        return host == "localhost" or host.endswith(".local")

    def _make_endpoint(
        self,
        *endpoint: str,
        query: dict[str, Any] | None = None,
    ) -> URL:
        return self.url.resolve(
            "/",
            self.api_version,
            *endpoint,
            query=query,
        )

    def _make_auth_endpoint(
        self,
        *endpoint: str,
        query: dict[str, Any] | None = None,
    ) -> URL:
        return self.auth_url.resolve(
            "/",
            self.auth_version,
            *endpoint,
            query=query,
        )

    def _make_execution_endpoint(
        self,
        agent: str | None = None,
        task: str | None = None,
        *,
        deployed_task_url: str | URL | None = None,
        environment: str | None = None,
        version: str | None = None,
        allow_cross_origin: bool = False,
    ) -> URL:
        # this method creates an endpoint to execute a deployed task
        if not self.url:
            raise ClientError("no Endeavor URL has been configured")

        if deployed_task_url is not None:
            ignored = [
                name
                for name, value in {
                    "agent": agent,
                    "task": task,
                    "environment": environment,
                    "version": version,
                }.items()
                if value is not None
            ]

            if ignored:
                warnings.warn(
                    f"{', '.join(ignored)} will be ignored because "
                    "deployed_task_url was provided",
                    UserWarning,
                )

            endpoint = (
                deployed_task_url
                if isinstance(deployed_task_url, URL)
                else URL.parse(deployed_task_url)
            )

            endpoint_origin = _url_origin(endpoint)
            configured_origin = _url_origin(self.url)

            if not allow_cross_origin and endpoint_origin != configured_origin:
                raise ValueError(
                    "deployed_task_url must use the configured Endeavor origin"
                )

            return endpoint

        if agent is None or task is None:
            raise ValueError(
                "agent and task are required when deployed_task_url is not provided"
            )

        parts: list[str] = []
        if environment is not None:
            parts.append(_validate_path_component(environment, "environment"))
        parts.extend(
            [
                _validate_path_component(agent, "agent"),
                _validate_path_component(task, "task"),
            ]
        )
        if version is not None:
            parts.append(_validate_semver(version))
        return self.url.resolve("/", "api", *parts)

    def _request(
        self,
        method: str,
        *endpoint: str,
        data: Any | None = None,
        query: dict[str, Any] | None = None,
        extra_headers: dict[str, Any] | None = None,
        files: Mapping[str, Any] | None = None,
        require_authentication: bool = True,
        stream: bool = False,
        resolved_url: URL | None = None,
        raw: bool = False,
    ) -> dict | Response | bytes | None:
        headers = self._pre_flight(
            require_authentication=require_authentication,
        )
        headers.update(extra_headers or {})

        if resolved_url is not None:
            url = resolved_url
        else:
            url = self._make_endpoint(
                *endpoint,
                query=query,
            )

        files = files or None

        if files is not None:
            rep = self.session.request(
                method,
                str(url),
                data=data,
                files=files,
                headers=headers,
                timeout=self.timeout,
                stream=stream,
            )
        else:
            rep = self.session.request(
                method,
                str(url),
                json=data,
                headers=headers,
                timeout=self.timeout,
                stream=stream,
            )

        return self.handle(rep, stream=stream, raw=raw)

    def _pre_flight(self, require_authentication: bool = True) -> dict[str, str]:
        if not self.url:
            raise ClientError("no Endeavor URL has been configured")

        request_headers = {}
        request_headers.update(self._headers)

        if require_authentication:
            request_headers.update(self._authentication_headers())
        return request_headers

    def _authentication_headers(self) -> dict[str, str]:
        if not self.is_authenticated():
            # We need to reauthenticate, determin if we can refresh our credentials
            if self.is_refreshable():
                self._creds = self._reauthenticate()
            else:
                self._creds = self._authenticate()

        return {"Authorization": "Bearer " + str(self._creds.access_token)}

    def _authenticate(self) -> Credentials:
        if not self.client_id or not self.client_secret:
            raise AuthenticationError("no client id or secret specified")

        apikey = {"client_id": self.client_id, "client_secret": self.client_secret}
        endpoint = self._make_auth_endpoint("authenticate")
        headers = self._pre_flight(require_authentication=False)

        logger.debug(f"POST {endpoint!r}")
        rep = self.session.post(
            str(endpoint), json=apikey, headers=headers, timeout=self.timeout
        )

        rep = self.handle(rep)
        return Credentials(rep["access_token"], rep["refresh_token"])

    def _reauthenticate(self) -> Credentials:
        if not self._creds.refresh_token:
            raise AuthenticationError("no refresh token available")

        refresh = {"refresh_token": str(self._creds.refresh_token)}
        endpoint = self._make_auth_endpoint("reauthenticate")
        headers = self._pre_flight(require_authentication=False)

        logger.debug(f"POST {endpoint!r}")
        rep = self.session.post(
            str(endpoint), json=refresh, headers=headers, timeout=self.timeout
        )

        rep = self.handle(rep)
        return Credentials(rep["access_token"], rep["refresh_token"])
