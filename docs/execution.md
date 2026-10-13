# Executing deployed Tasks

[Documentation home](README.md) · [Getting started](getting-started.md) ·
[Concepts](concepts.md) · [Lifecycle](lifecycle.md)

Execution requires a deployed Release. Use the high-level `Endeavor.run()` for
normal application code and the low-level `Client.execute()` when response
headers, bytes, or explicit cross-origin access are required.

## High-level execution

`Endeavor.run()` has this signature:

```python
endeavor.run(
    agent=None,
    task=None,
    context=None,
    *,
    deployed_task_url=None,
    environment=None,
    version=None,
    files=None,
)
```

Select a deployed Task by Agent and Task slug or ID:

```python
result = endeavor.run(
    "northwind-triage",
    "classify-request",
    context={
        "subject": "Example delivery question",
        "message": "When would a fictional order arrive?",
    },
)
```

To select a particular deployment, add an Environment slug or ID and a
semantic Version:

```python
result = endeavor.run(
    "northwind-triage",
    "classify-request",
    context={"message": "Please classify this example."},
    environment="staging",
    version="1.4.0",
)
```

`version` must be valid SemVer. Agent, Task, and Environment selectors must
each be a single safe URL path component.

## Complete deployed-task URLs

Instead of selectors, pass an absolute deployed URL:

```python
result = endeavor.run(
    deployed_task_url=(
        "https://studio.example.test/api/"
        "staging/northwind-triage/classify-request/1.4.0"
    ),
    context={"message": "Please classify this example."},
)
```

The URL must use the same origin as the configured Endeavor URL. Origin means
the same scheme, hostname, and effective port. If `deployed_task_url` is
provided together with Agent, Task, Environment, or Version selectors, the
selectors are ignored and Guidelight emits a `UserWarning`.

`Endeavor.run()` intentionally has no cross-origin override. For a trusted
deployment URL on another origin, opt in explicitly through the low-level
client:

```python
response = endeavor.client.execute(
    deployed_task_url=(
        "https://runtime.example.test/api/"
        "staging/northwind-triage/classify-request/1.4.0"
    ),
    context={"message": "Please classify this example."},
    allow_cross_origin=True,
    raw=True,
)
```

This opt-in sends the authenticated request to the supplied origin. Use it
only for a URL you trust. Absolute URLs containing user information are
rejected.

## Files and multipart requests

Both APIs accept a `files` mapping compatible with `requests`. When files are
present, Guidelight sends multipart form data and JSON-serializes `context`
into a form field named `context`:

```python
with open("sample-invoice.pdf", "rb") as document:
    result = endeavor.run(
        "northwind-documents",
        "extract-invoice",
        context={"instruction": "Extract the fictional invoice total."},
        environment="staging",
        version="2.0.0",
        files={"sample-invoice.pdf": document},
    )
```

Without files, `context` is sent directly as the JSON request body; `None`
becomes an empty object.

## Response decoding

`Endeavor.run()` requests the raw HTTP response internally, then decodes it:

- `application/json` becomes the corresponding Python value.
- `text/plain` becomes `str`, honoring the response encoding.
- HTTP 204 becomes `None`.
- another successful content type raises `UnsupportedResponseType`.

Client methods raise Guidelight exceptions when authentication or HTTP requests fail.

## Low-level execution and raw responses

`Client.execute()` adds two keyword-only controls:

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

Selector, version, URL, and multipart behavior match `Endeavor.run()`.
Response behavior differs:

- with `raw=False` (the default), `application/json` is decoded and every
other successful response body is returned as `bytes`;
- with `raw=True`, a successful non-204 call returns the underlying
`requests.Response`, giving access to headers, status, `.content`, `.text`,
and `.json()`;
- HTTP 204 returns `None` in either mode.

```python
response = endeavor.client.execute(
    "northwind-triage",
    "classify-request",
    context={"message": "Please classify this example."},
    environment="staging",
    version="1.4.0",
    raw=True,
)

content_type = response.headers.get("Content-Type")
payload = response.content
```



## `Release.test()` is different

`Releases.test()` is a release-scoped smoke-test action:

```python
from guidelight.models import ReleaseTest

smoke = endeavor.releases.test(
    release.id,
    ReleaseTest(input="Classify this fictional request."),
)

if smoke.error:
    raise RuntimeError(smoke.error)
print(smoke.output_text)
```

It addresses a specific Release ULID and returns `ReleaseTestResult` with
`output_text` and `error`. It does not share the general execution signature,
does not support files or arbitrary response decoding, and is not a substitute
for calling the public deployed Task through `Endeavor.run()`.