# Guidelight

**A library for developing task-oriented AI systems that integrate with Endeavor.**

## Getting Started

Install Guidelight:

```console
pip install guidelight
```

Configure an Endeavor API key:

```dotenv
ENDEAVOR_URL=https://guidelight.dev
ENDEAVOR_AUTH_URL=https://auth.guidelight.dev
ENDEAVOR_CLIENT_ID=your-client-id
ENDEAVOR_CLIENT_SECRET=your-client-secret
```

`ENDEAVOR_AUTH_URL` is the authentication service's base URL. Guidelight adds the `/v1/authenticate` or `/v1/reauthenticate` path. It is optional for hosted deployments. For standard hosted deployments, Guidelight can derive the authentication host by adding the
`auth.` subdomain. For localhost or a custom authentication host, set `ENDEAVOR_AUTH_URL` explicitly.

Create a high-level Endeavor SDK:

```python
import guidelight as gdl

endeavor = gdl.connect()
print(endeavor.status())
```

Use `gdl.client()` when direct access to the low-level HTTP client is needed:

```python
client = gdl.client()
print(client.status())
```

The high-level SDK also exposes its authenticated client:

```python
client = endeavor.client
```

## Low-level Client

The low-level client accepts endpoint path components and automatically adds
the configured API version.

### GET

```python
agents = client.get(
    "agents",
    query={"page_size": 10, "offset": 0},
)
```

### POST

```python
agent = client.post(
    {
        "name": "Demo Support Agent",
        "description": "A demonstration Agent.",
    },
    "agents",
)
```

### PUT

```python
updated_agent = client.put(
    {
        "name": "Updated Demo Support Agent",
        "description": "An updated demonstration Agent.",
    },
    "agents",
    "<agent-ulid>",
)
```

### PATCH

Use PATCH only with an endpoint that supports partial updates:

```python
environment = client.patch(
    {
        "description": "Updated development environment.",
    },
    "environments",
    "<environment-ulid-or-slug>",
)
```

### DELETE

```python
client.delete("agents", "<agent-ulid>")
```

### Execute a deployed Task

Execute by Agent and Task slug or ID:

```python
result = client.execute(
    "demo-support-agent",
    "summarize-message",
    context={
        "message": "Summarize this example customer message.",
    },
)
```

Select a deployed Release by Environment and semantic Version:

```python
result = client.execute(
    "demo-support-agent",
    "summarize-message",
    context={"message": "Summarize this text."},
    environment="production",
    version="1.2.3",
)
```

Execute using a complete deployed-task URL. **NOTE:** Cross-origin URLs are rejected unless explicitly enabled.

```python
result = client.execute(
    deployed_task_url=(
        "https://guidelight.dev/api/"
        "demo-support-agent/summarize-message"
    ),
    context={"message": "Summarize this text."},
)
```


Upload a file using multipart form data:

```python
with open("example.pdf", "rb") as document:
    result = client.execute(
        "demo-document-agent",
        "extract-document-text",
        context={"instruction": "Extract the important details."},
        files={
            "example.pdf": document,
        },
    )
```

`Client.execute()` returns the decoded JSON body or raw response bytes by
default. Pass `raw=True` when response headers and the underlying
`requests.Response` are needed.

## High-level Endeavor SDK

The high-level SDK provides typed resource operations and decodes deployed-task
responses according to their response content type.

### List and retrieve Agents

```python
page = endeavor.agents.list(
    page_size=10,
    offset=0,
    order_by="name",
)

for agent in page:
    print(agent.id, agent.name, agent.slug)

agent = endeavor.agents.get("demo-support-agent")
```

Iterate across all Agent pages:

```python
for agent in endeavor.agents.iterate(page_size=25):
    print(agent.name)
```

### Create, update, and delete an Agent

```python
agent = endeavor.agents.create(
    name="Demo Support Agent",
    description="A temporary demonstration Agent.",
)

agent = endeavor.agents.update(
    agent.id,
    name="Updated Demo Support Agent",
    description="An updated temporary demonstration Agent.",
)

endeavor.agents.delete(agent.id)
```

### Run a deployed Task

```python
result = endeavor.run(
    "demo-support-agent",
    "summarize-message",
    context={
        "message": "Summarize this example customer message.",
    },
)
```

Select an Environment and Version:

```python
result = endeavor.run(
    "demo-support-agent",
    "summarize-message",
    context={"message": "Summarize this text."},
    environment="production",
    version="1.2.3",
)
```

Use a complete deployed-task URL:

```python
result = endeavor.run(
    deployed_task_url=(
        "https://guidelight.dev/api/"
        "demo-support-agent/summarize-message"
    )
    context={"message": "Summarize this text."},
)
```

Run a deployed task with a file:

```python
with open("example.pdf", "rb") as document:
    result = endeavor.run(
        "demo-document-agent",
        "extract-document-text",
        context={"instruction": "Extract the important details."},
        files={
            "example.pdf": document,
        },
    )
```

`Endeavor.run()` returns `str` for `text/plain` responses and decoded Python
values for `application/json` responses.
