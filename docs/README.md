# Guidelight documentation

Guidelight is a Python SDK for building, evaluating, releasing, and running
task-oriented AI systems on Endeavor.

## Guides

- [Getting started](getting-started.md) — install the package, configure
  authentication, and choose the high- or low-level API.
- [Core concepts](concepts.md) — understand the resource graph, manager scopes,
  references, typed models, and pagination.
- [Executing deployed Tasks](execution.md) — use `Endeavor.run()` or
  `Client.execute()`, select a deployment, upload files, and decode responses.
- [Resource lifecycle](lifecycle.md) — create an Agent hierarchy, execute an
  Experiment, deploy a Release, and clean up safely.
- [Low-level client](client.md) — configure `Client`, call endpoint methods,
  execute deployed Tasks, and work with raw responses and errors.
- [Resource reference](resources/README.md) — look up manager methods, model
  fields, scopes, actions, and deletion dependencies.

## Which API should I use?

Start with `guidelight.connect()`. It returns an `Endeavor` object whose
resource managers validate request and response data with Pydantic models:

```python
import guidelight as gdl

endeavor = gdl.connect()
agents = endeavor.agents
```

The `Endeavor` object exposes:

- `agents`, `test_cases`, `generations`, and `releases` as top-level resource
  managers;
- `client` for authenticated low-level access;
- `status()` for service status; and
- `run()` for content-type-aware deployed Task execution.

Use `guidelight.client()` only when you need direct HTTP endpoint access or
low-level execution options such as raw responses or explicit cross-origin
execution:

```python
client = gdl.client()
```

See the [low-level client guide](client.md) for request signatures, endpoint
construction, authentication behavior, and response handling. For typed
resource operations, use the [resource reference](resources/README.md).

Both entry points authenticate during construction. The examples in these
guides use fictional names and placeholders; they are not intended to be run
unchanged against a live Endeavor account.

