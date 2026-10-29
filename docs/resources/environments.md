# Environments

[Resource index](README.md) · [Core concepts](../concepts.md) ·
[Lifecycle](../lifecycle.md)

An Environment identifies where a Release is deployed. Environments are
global configuration resources; Releases refer to them when they are created.

## Manager

```python
environments = endeavor.environments
```

The manager provides:

- `list(provider_id=None, **options) -> Page[Environment]`
- `iterate(**options)`
- `create(request=None, **fields) -> Environment`
- `get(ref) -> Environment`
- `update(ref, request=None, **fields) -> Environment`
- `patch(ref, request=None, **fields) -> Environment`
- `delete(ref) -> None`

`list()` supports the `provider_id` filter together with `page_size`, `offset`,
and `order_by`. Environment references are ULID-only unless the server route
explicitly documents slug support.

## Request models

```python
from guidelight.models import (
    EnvironmentCreate,
    EnvironmentPatch,
    EnvironmentUpdate,
)

environment = endeavor.environments.create(
    EnvironmentCreate(
        name="Staging",
        slug="staging",
        description="Pre-production deployment environment.",
    )
)

environment = endeavor.environments.patch(
    environment.id,
    EnvironmentPatch(description="Updated staging environment."),
)
```

`EnvironmentUpdate` is a complete PUT representation. `EnvironmentPatch`
allows partial updates but rejects an empty request. Server-managed IDs and
timestamps are response-only fields. When assigning a Provider, pass its ID
in the nested reference:

```python
environment = endeavor.environments.patch(
    environment.id,
    EnvironmentPatch(provider={"id": provider.id}),
)
```

Environment PATCH requests may set `is_default=True`, but Endeavor does not
accept `is_default=False` as a PATCH action.

