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
prompts = [
    {
        "role": "system",
        "template": (
            "Classify the customer request and recommend the next action."
        ),
    },
    {
        "role": "user",
        "template": (
            "Subject: {{ .subject }}\n"
            "Customer message: {{ .message }}"
        ),
    },
]

result = endeavor.run(
    "northwind-triage",
    "classify-request",
    context={
        "subject": "Example delivery question",
        "message": "When would a fictional order arrive?",
    },
)
```

### Context keys and prompt variables

The `prompts` variable illustrates the prompts configured on the Experiment
before its Release was created and deployed. It is not passed to
`endeavor.run()` because the deployed Release already contains those prompts.
The run call supplies the values used to render them.

The value passed to `context` becomes the Task context; the Python argument
name does not create another key inside that value. Here, the `"subject"` and
`"message"` keys correspond directly to `{{ .subject }}` and
`{{ .message }}` in the configured Go template.

If a prompt instead uses `{{ .context }}`, supply a matching key:

```python
prompts = [
    {
        "role": "system",
        "template": "Classify the customer request.",
    },
    {
        "role": "user",
        "template": "{{ .context }}",
    },
]

result = endeavor.run(
    "northwind-triage",
    "classify-request",
    context={"context": "When would a fictional order arrive?"},
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

Without files, the request body wraps the supplied context as
`{"context": <context>}`; passing `None` sends `{"context": {}}`.

## Response decoding

`Endeavor.run()` requests the raw HTTP response internally, then decodes it:

- `application/json` becomes the corresponding Python value.
- `text/plain` becomes `str`, honoring the response encoding.
- `multipart/form-data` becomes a typed `ExecutionResult` containing the output and returned file bytes.
- HTTP 204 becomes `None`.
- another successful content type raises `UnsupportedResponseType`.

Client methods raise Guidelight exceptions when authentication or HTTP requests fail.

## Multimodal execution results

Use `Endeavor.run_with_result()` to validate and decode the
deployed Task output. It accepts both ordinary JSON output and multipart output
with generated files:

```python
result = endeavor.run_with_result(
    "image-agent",
    "generate-image",
    context={"prompt": "Generate a blue circle."},
    environment="production",
)

if result is not None:
    print(result.output, result.outcome)
    print(result.model.slug, result.usage.total_tokens)
    for attachment in result.attachments:
        print(attachment.filename, attachment.content_type)
        with open("generated/" + attachment.filename, "wb") as output:
            output.write(attachment.data or b"")
```

`ExecutionResult` models the response emitted by Horizon. Its fields are
`usage`, `model`, `output`, `mime_type`, `capabilities`, `actions`, `started`,
`finished`, `outcome`, and `attachments`. Each execution attachment contains
`id`, `filename`, `content_type`, `url`, and `data` when supplied by the
runtime.

Execution attachments are not persisted Endeavor `Media` objects. The immediate
response does not include a Generation ID, Release ID, Experiment ID, or
persisted Media metadata. Retrieve a known Generation separately when that
resource information is needed.

`run()` remains backward-compatible for JSON and text responses. For a
multipart response it returns the same typed `ExecutionResult` so generated
files are not exposed as undifferentiated multipart bytes. The provider and
model must actually return media; a catalog entry alone does not guarantee
that a deployed Task produces an attachment.

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



Release testing is performed in the Endeavor UI sandbox. Programmatic callers
should use the deployed endpoint through `Endeavor.run()` or
`Endeavor.run_with_result()` instead.