# Getting started

[Documentation home](README.md) · [Concepts](concepts.md) ·
[Execution](execution.md) · [Lifecycle](lifecycle.md)

## Install

```console
pip install guidelight
```

Guidelight reads a local `.env` file as well as process environment variables
when values are not passed explicitly.

## Configure authentication

Set the Endeavor API URL and API-key credentials:

```dotenv
ENDEAVOR_URL=https://example.test
ENDEAVOR_AUTH_URL=https://auth.example.test
ENDEAVOR_CLIENT_ID=example-client-id
ENDEAVOR_CLIENT_SECRET=example-client-secret
```

`ENDEAVOR_AUTH_URL` is the authentication service **base URL**, not the
authentication endpoint. Guidelight appends `/v1/authenticate` when obtaining
credentials and `/v1/reauthenticate` when refreshing them. For example, the
configuration above authenticates at
`https://auth.example.test/v1/authenticate`.

The same settings can be provided as arguments:

```python
import guidelight as gdl

endeavor = gdl.connect(
    url="https://studio.example.test",
    auth_url="https://auth.example.test",
    client_id="example-client-id",
    client_secret="example-client-secret",
    timeout=30,
)
```

`timeout` may also be a `requests`-style timeout tuple. When it is omitted,
Guidelight uses a 10-second connection timeout and a 30-second read timeout.

> Connecting performs authentication immediately. Keep credentials out of
> source control, and replace all values above before using a real service.



## Connect to the high-level SDK

The recommended entry point is `connect()`:

```python
import guidelight as gdl

endeavor = gdl.connect()

page = endeavor.agents.list(page_size=20)
for agent in page:
    print(agent.name)
```

The returned `Endeavor` object exposes typed managers for Agents, global Test
Cases, Generations, and Releases. Child managers are reached from their
parents; see [Core concepts](concepts.md#manager-scope).

`endeavor.status()` checks server status. It is a network call even though the
status endpoint itself does not require authentication.

## Use the low-level client

Use `client()` for an endpoint not represented by a resource manager:

```python
client = gdl.client()

body = client.get(
    "agents",
    query={"page_size": 20, "offset": 0},
)
```

Low-level resource requests are rooted at the configured API version,
currently `/v2` by default. Do not add `v2` to endpoint components yourself.
The authenticated low-level client is also available as `endeavor.client`.

## Next steps

1. Read [Core concepts](concepts.md) before creating resources.
2. Follow the [Resource lifecycle](lifecycle.md) to evaluate and deploy a Task.
3. Use [Executing deployed Tasks](execution.md) after a Release is deployed.

