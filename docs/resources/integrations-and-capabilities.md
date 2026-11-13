# Integrations and Experiment Capabilities

[Resource index](README.md) · [Core concepts](../concepts.md) ·
[Lifecycle](../lifecycle.md) · [Execution](../execution.md)

## Integrations

An Integration represents an external MCP server available to Endeavor. The
SDK exposes Integration operations through `endeavor.integrations`.
MCP servers that require no authentication can connect without user action.
When an Integration enters `auth_required`, a user must sign in to Endeavor
and authorize the MCP server in the UI before it can be used.

```python
integration = endeavor.integrations.create(
    name="Notion",
    endpoint="https://mcp.notion.com/mcp",
    wait=True,
)

for tool in integration.tools or []:
    print(tool.name, tool.id)
```

The manager supports:

- `list()` and `iterate()` for discovered Integrations.
- `get(ref)` for Integration details and discovered MCP prompts, resources,
  and tools.
- `create(..., wait=False)` for nonblocking creation.
- `create(..., wait=True)` and `wait_for_status()` for bounded polling. When
  authorization is required, open the Endeavor URL provided in the warning
  and complete authorization in the browser. Polling continues during this
  process; once the Integration reaches `connected`, the method returns and
  subsequent operations can proceed.
- `update()`, `patch()`, and `delete()` for Integration management.
- `refresh()` to queue discovery without waiting or returning an updated
  Integration. Call `wait_for_status()` afterward when subsequent operations
  require discovery to finish.

Methods that address one Integration accept either an Integration model or its
ULID. Malformed references are rejected before an HTTP request is sent.
Create, update, and patch requests require an absolute `http` or `https`
endpoint with a valid host.

Integration list and mutation responses omit discovered prompt, resource, and
tool details. Their `prompts`, `resources`, and `tools` fields remain `None`,
and `catalog_included` is `False`; this means “not loaded,” not “the catalog is
empty.” `get()`, `wait_for_status()`, and `create(wait=True)` return detail
responses with those fields normalized to lists and `catalog_included=True`.

Discovery is asynchronous. `pending` and `initializing` are nonterminal
states. `auth_required` and `reg_required` emit warnings containing the
Endeavor Integration URL so the caller can complete setup in the UI while
polling continues. Successful discovery ends in `connected`; `error`,
`disconnected`, and `disabled` are terminal failures.

```python
integration = endeavor.integrations.create(
    name="Notion",
    endpoint="https://mcp.notion.com/mcp",
    wait=False,
)
print(integration.status)
```

The supported Integration response does not include OAuth secrets or access
tokens, and Guidelight does not declare credential fields on the response
model. Unknown server fields are preserved in the model's `extra` mapping, so
do not log that mapping without reviewing its contents.
`OAuthCredentials.client_secret` is masked locally with `SecretStr` and is
only exposed at explicit JSON request serialization time.

## Experiment capabilities

An Integration advertises MCP capabilities. An Experiment selects specific
capability IDs for use by a deployed Release:

```python
from guidelight.models import ExperimentCapability

tool = integration.tools[0]
experiments.capabilities(
    experiment.id,
    [ExperimentCapability(type="integration_tool", id=tool.id)],
)
```

Supported capability types are:

- `integration_prompt`
- `integration_resource`
- `integration_tool`

Capability selection uses replacement semantics. The submitted list becomes
the complete selection; it is not merged with the existing selection. Pass an
empty typed update to clear all selections:

```python
from guidelight.models import ExperimentCapabilityUpdate

experiments.capabilities(
    experiment.id,
    ExperimentCapabilityUpdate(),
)
```

The operation sends a `PUT` request to the Experiment capability association
endpoint. Capability IDs must refer to entries advertised by the Integration.
The selected capabilities are part of the Experiment configuration and are
snapshotted by a Release when that Experiment is released.

## Execution and testing

After selecting capabilities, configure the Experiment, associate Test Case
Versions, transition it to `ready`, and deploy a Release. Programmatic
execution uses `Endeavor.run()` or `run_with_result()`.

