# Models and Governance

[Resource index](README.md) · [Core concepts](../concepts.md) ·
[Lifecycle](../lifecycle.md)

## Model catalog

Models are read-only catalog resources. Obtain the global catalog with:

```python
models = endeavor.models
```

Provider-scoped model access is also available:

```python
models = endeavor.providers.models(provider)
```

The manager provides:

- `list(**filters) -> Page[Model]`
- `iterate(**filters)`
- `get(ref) -> Model`
- `usage(ref) -> ModelUsage`

Supported filters include provider, author, publication dates, input and
output modalities, context size, capabilities, cost and rate limits,
moderation, API/auth type, restriction, and selected model ID.

```python
page = endeavor.models.list(
    provider_id=provider.id,
    input_modality="Text",
    context_size_above=32000,
    page_size=100,
)

for model in page:
    print(model.id, model.name)

usage = endeavor.models.usage(page.items[0].id)
```

There are no `create()`, `update()`, `patch()`, or `delete()` methods for
Models. Catalog fields such as pricing, limits, usage, credentials, and
deployment metadata are response-only. UI-only HTML model-option endpoints
and the UI-only model-environment endpoint are not exposed by the SDK.

## Governance policies

Global governance policies are accessed through:

```python
policies = endeavor.governance_policies
```

Provider-scoped policies are listed through a Provider:

```python
policies = endeavor.providers.governance(provider)
```

The global manager provides:

- `list(active=None, **options) -> Page[GovernancePolicy]`
- `iterate(**options)`
- `create(request=None, **fields) -> GovernancePolicy`
- `get(ref) -> GovernancePolicy`
- `patch(ref, request=None, **fields) -> GovernancePolicy`
- `delete(ref) -> None`

The provider-scoped manager supports only `list()` and `iterate()` because
Endeavor does not expose provider-scoped mutation or detail routes. Create a
policy for a Provider through the global manager and set `provider_id` in the
request.

```python
from guidelight.models import GovernancePolicyCreate, GovernancePolicyPatch

policy = policies.create(
    GovernancePolicyCreate(
        name="Production policy",
        policy_type="model",
        provider_id=provider.id,
        constraints={"max_cost": 1.0},
    )
)

policy = policies.patch(
    policy.id,
    GovernancePolicyPatch(active=False),
)
```

Writable policy types are currently `license` and `model`. Constraints must be
a nonempty JSON-compatible value; their exact structure depends on the policy
type and target Endeavor deployment.

