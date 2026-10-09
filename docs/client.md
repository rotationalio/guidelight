# Low-level client

[Documentation home](README.md) · [Getting started](getting-started.md) ·
[Execution](execution.md) · [Resource reference](resources/README.md)

Use the low-level `Client` for direct HTTP endpoint access, response metadata,
or execution controls that are not exposed by `Endeavor.run()`.

## Construct a client

The recommended constructor is `guidelight.client()`:

```python
import guidelight as gdl

client = gdl.client()
```

It accepts `url`, `client_id`, `client_secret`, `auth_url`, and `timeout`.
Missing values are loaded from a local `.env` file and then from these
environment variables:

```dotenv
ENDEAVOR_URL=https://studio.example.test
ENDEAVOR_AUTH_URL=https://auth.example.test
ENDEAVOR_CLIENT_ID=example-client-id
ENDEAVOR_CLIENT_SECRET=example-client-secret
```

If `auth_url` and `ENDEAVOR_AUTH_URL` are both omitted, the authentication base
URL falls back to the main Endeavor URL. Set an explicit authentication URL
when authentication and API traffic use different origins. Guidelight appends
`/v1/authenticate` or `/v1/reauthenticate`; do not include either path in the
configured base URL.

The factory performs an authenticated preflight before returning. A missing
URL raises `ClientError`; missing API-key material raises
`AuthenticationError`; authentication HTTP failures are raised immediately.

`Client` can also be constructed directly:

```python
from guidelight import Client

client = Client(
    url="https://studio.example.test",
    auth_url="https://auth.example.test",
    client_id="example-client-id",
    client_secret="example-client-secret",
    timeout=30,
)
```

Direct construction reads process environment variables for omitted values but
does not load `.env` itself. It also supports connection-pool, retry, API
version, and authentication version arguments. Authentication is lazy: the
first authenticated request obtains credentials. The default timeout is
`(10.0, 30.0)` for connection and read timeouts.

An authenticated client is also available as `endeavor.client`.

## Status

```python
status = client.status()
```

`status()` sends `GET /v2/status` without requiring an authentication header.
It is still a network request and requires a configured Endeavor URL. Note that
`guidelight.client()` has already authenticated during its factory preflight.

## Endpoint requests

The request methods have these public signatures:

```python
client.get(*endpoint, query=None, require_authentication=True, **options)
client.post(data, *endpoint, query=None, require_authentication=True, **options)
client.put(data, *endpoint, query=None, require_authentication=True, **options)
client.patch(data, *endpoint, query=None, require_authentication=True, **options)
client.delete(*endpoint, query=None, require_authentication=True, **options)
```

Pass URL path components as separate positional strings. Guidelight places
them below the configured API version (`/v2` by default), so do not include
`v2`, a complete URL, or leading slashes:

```python
page = client.get(
    "agents",
    query={"page_size": 10, "offset": 0},
)

created = client.post(
    {
        "name": "Atlas Assistant",
        "description": "A fictional example Agent.",
    },
    "agents",
)

updated = client.put(
    {
        "name": "Atlas Assistant",
        "description": "An updated fictional Agent.",
    },
    "agents",
    "<agent-ulid>",
)

patched = client.patch(
    {"description": "A partially updated development Environment."},
    "environments",
    "<environment-ulid-or-slug>",
)

client.delete("agents", "<agent-ulid>")
```

`query` is URL-encoded and supports sequence values. For POST, PUT, and PATCH,
`data` is sent as the JSON request body by default. Common advanced options
include `extra_headers`, `files`, `stream`, and `raw`. Supplying `files`
switches the request to multipart form data. A streamed or raw successful
response is returned as a `requests.Response`.

Set `require_authentication=False` only for an endpoint known to be public.
The default obtains or refreshes credentials as needed and sends a bearer
token.

## Execute a deployed Task

`execute()` has this signature:

```python
client.execute(
    agent=None,
    task=None,
    context=None,
    *,
    deployed_task_url=None,
    environment=None,
    version=None,
    files=None,
    raw=False,
    allow_cross_origin=False,
)
```

Select a deployment with Agent and Task slugs or IDs:

```python
result = client.execute(
    "atlas-assistant",
    "summarize-note",
    context={"note": "A fictional project update."},
    environment="staging",
    version="1.4.0",
)
```

`environment` is optional and prefixes the Agent and Task in the deployed
route. `version` is optional, follows the Task, and must be valid semantic
versioning. Every selector must be one safe URL path component.

Alternatively, provide an absolute deployed-task URL:

```python
result = client.execute(
    deployed_task_url=(
        "https://studio.example.test/api/"
        "staging/atlas-assistant/summarize-note/1.4.0"
    ),
    context={"note": "A fictional project update."},
)
```

When `deployed_task_url` is present, Agent, Task, Environment, and Version
selectors are ignored with a `UserWarning`. The URL must be absolute HTTP(S),
must not contain user information, and by default must have the same origin as
the configured Endeavor URL. Same origin means matching scheme, hostname, and
effective port.

For a trusted deployment on another origin, the low-level client can opt in:

```python
result = client.execute(
    deployed_task_url=(
        "https://runtime.example.test/api/"
        "atlas-assistant/summarize-note"
    ),
    context={"note": "A fictional project update."},
    allow_cross_origin=True,
)
```

This sends the authenticated request, including its bearer token, to the
supplied origin. Use the override only for a URL you trust.
`Endeavor.run()` does not support `allow_cross_origin`.

With `files`, execution uses multipart form data and JSON-serializes `context`
into a form field named `context`:

```python
with open("fictional-note.txt", "rb") as note:
    result = client.execute(
        "atlas-assistant",
        "summarize-file",
        context={"instruction": "Summarize the attached example."},
        files={"fictional-note.txt": note},
    )
```

Without files, `context` is the JSON request body; `None` becomes `{}`.

## Responses and errors

For ordinary methods and `execute(raw=False)`:

- `application/json` responses are decoded to Python values.
- Other successful response bodies are returned as `bytes`.
- HTTP 204 returns `None`.

With `raw=True`, or `stream=True` on ordinary request methods, successful
non-204 calls return `requests.Response`.

HTTP 401 and 403 raise `AuthenticationError`, HTTP 404 raises `NotFound`, other
4xx responses raise `ClientError`, and 5xx responses raise `ServerError`.
Invalid selectors and unsafe execution URLs raise `ValueError`. Network,
timeout, and lower-level HTTP errors from `requests` may also propagate.

For normal high-level execution and content-type-aware text decoding, see
[Executing deployed Tasks](execution.md).

## Advanced client state

The Client also exposes these state helpers:

- `is_authenticated()` reports whether the current access token is valid.
- `is_refreshable()` reports whether the current refresh token is valid.
- `is_localhost()` reports whether the configured host is `localhost` or uses
  a `.local` domain.

`handle(response, *, stream=False, raw=False)` is the response-processing
method used internally by requests. Most callers should let `get()`, `post()`,
`put()`, `patch()`, `delete()`, or `execute()` invoke it.

Direct `Client(...)` construction additionally accepts `pool_connections`,
`pool_maxsize`, `max_retries`, `api_version`, and `auth_version`. Prefer the
defaults unless the application needs custom transport pooling, retry
behavior, or a non-default server API version.
