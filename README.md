# Guidelight

Guidelight is a Python SDK for building, evaluating, releasing, and running
task-oriented AI systems on Endeavor.

## Install

```console
pip install guidelight
```

## Configure

Set an Endeavor URL and API-key credentials in the environment or a local
`.env` file:

```dotenv
ENDEAVOR_URL=https://example.test
ENDEAVOR_AUTH_URL=https://auth.example.test
ENDEAVOR_CLIENT_ID=example-client-id
ENDEAVOR_CLIENT_SECRET=example-client-secret
```

`ENDEAVOR_AUTH_URL` is optional when authentication uses the same origin as
`ENDEAVOR_URL`. Set it when the authentication service uses another origin.

## Connect and list Agents

```python
import guidelight as gdl

endeavor = gdl.connect()

for agent in endeavor.agents.list(page_size=10):
    print(agent.name)
```

Resource managers return typed models:

```python
from guidelight.models import Agent

agent: Agent = endeavor.agents.get("atlas-assistant")
print(agent.id, agent.slug)
```

Use `guidelight.client()` when direct low-level endpoint access is needed.

## Run a deployed Task

```python
result = endeavor.run(
    "atlas-assistant",
    "summarize-note",
    context={"note": "A fictional project update."},
)
```



## Documentation

- [Documentation home](docs/README.md)
- [Getting started](docs/getting-started.md)
- [Core concepts](docs/concepts.md)
- [Executing deployed Tasks](docs/execution.md)
- [Resource lifecycle](docs/lifecycle.md)
- [Low-level client](docs/client.md)
- [Resource reference](docs/resources/README.md)

