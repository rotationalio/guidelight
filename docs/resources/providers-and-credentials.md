# Providers and Credentials

[Resource index](README.md) · [Core concepts](../concepts.md) ·
[Getting started](../getting-started.md)

Providers describe external model services. Credentials belong to a Provider
and must remain provider-scoped for every operation.

## Providers

```python
providers = endeavor.providers
```

The manager provides:

- `list(**options) -> Page[Provider]`
- `iterate(**options)`
- `create(request=None, **fields) -> Provider`
- `get(ref) -> Provider`
- `update(ref, request=None, **fields) -> Provider`
- `patch(ref, request=None, **fields) -> Provider`
- `delete(ref) -> None`
- `default() -> Provider`
- `test_connectivity(ref) -> ProviderStatusResponse`
- `refresh_catalog(ref) -> None`
- `update_status(ref, status) -> None`
- `models(ref) -> Models`
- `credentials(ref) -> ProviderCredentials`
- `governance(ref) -> GovernancePolicies`

Provider references may be ULIDs or slugs. Provider status, usage, catalog
timestamps, and deployment metadata are response-only. Endeavor's Provider
status polling route is HTMX-only and is therefore not exposed by this
manager.

```python
from guidelight.models import ProviderCreate, ProviderCredentialCreate

provider = providers.create(
    ProviderCreate(
        name="OpenRouter",
        slug="openrouter",
        endpoint="https://openrouter.ai/api",
        catalog_url="https://openrouter.ai/models",
        credential=ProviderCredentialCreate(
            name="OpenRouter production",
            credentials={"type": "api_key", "api_key": "<secret>"},
        ),
    )
)

status = providers.test_connectivity(provider.id)
```

Every Provider creation requires an initial credential. `refresh_catalog()`
and `update_status()` return no response model and can change external or
server-managed state. Treat them as explicit operational actions.

## Credentials

Credentials are always obtained from a Provider:

```python
credentials = providers.credentials(provider)
```

The manager provides:

- `list(**options) -> Page[ProviderCredential]`
- `iterate(**options)`
- `create(request=None, **fields) -> ProviderCredential`
- `default() -> ProviderCredential`
- `update(ref, request=None, **fields) -> ProviderCredential`
- `patch(ref, request=None, **fields) -> ProviderCredential`
- `delete(ref) -> None`
- `test_connectivity(secret_ref) -> ProviderStatusResponse`

The parent Provider reference may be a ULID or slug. Credential
`secret_ref` values are ULIDs. Endeavor does not expose a general credential
detail route; use `list()` or `default()` to retrieve credential metadata.

```python
from guidelight.models import ProviderCredentialCreate

credential = credentials.create(
    ProviderCredentialCreate(
        name="OpenRouter production",
        credentials={"type": "api_key", "api_key": "<secret>"},
    )
)
```

Credential response models expose metadata only. Do not print, persist, or
return credential payloads, access tokens, or secret values from application
logs or AI-tool responses.

