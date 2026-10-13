# Releases

[Resource index](README.md) · [Core concepts](../concepts.md) ·
[Lifecycle](../lifecycle.md) · [Execution](../execution.md)

A Release promotes one Experiment for a Task into one Environment at a
version. A request can target multiple Environments, creating one independent
Release per Environment. Deployed execution can produce Release-associated
Generations.

## Obtaining a manager

```python
global_releases = endeavor.releases
task_releases = endeavor.agents.tasks(agent).releases(task)
```

Both managers can list and create. Task scope changes those collection routes.
Global creation must supply `task_id` in `ReleaseCreate`; Task-scoped creation
already identifies the Task.

## Releases manager API

- `list(**options) -> Page[Release]` lists the global or Task-scoped
  collection.
- `iterate(**options)` yields Releases across list pages.
- `get(ref) -> Release` gets one Release.
- `create(request=None, **fields) -> list[Release]` creates one Release per
  requested Environment. It always returns a list, even for one Environment.
- `update(ref, request=None, **fields) -> Release` replaces mutable deployment
  metadata with `ReleaseUpdate`.
- `patch(ref, request=None, **fields) -> Release` partially changes deployment
  metadata with `ReleasePatch`.
- `delete(ref) -> None` deletes the Release.
- `clone(ref, environments: list[str]) -> list[Release]` creates independent
  clones in the destination Environments.
- `deploy(ref) -> Release` deploys it using the server's clock.
- `retire(ref) -> Release` retires it using the server's clock.
- `test(ref, request=None, **fields) -> ReleaseTestResult` tests it.
- `generations(ref) -> ReleaseGenerations` returns its Generation list
  manager.

`list()` and `iterate()` support `page_size`, `offset`, and `order_by`, plus
these filters: `task_id`, `environment_id`, `experiment_id`, their plural
`task_ids`, `environment_ids`, and `experiment_ids` forms, `version`,
`version_min`, `version_max`, created and modified before/after ranges,
`deployed` and deployed before/after ranges, and `retired` and retired
before/after ranges.

Every method that addresses a specific Release requires a Release ULID:
`get`, `update`, `patch`, `delete`, `clone`, `deploy`, `retire`, `test`, and
`generations`. Release slugs are not supported and fail local validation.
Experiment, Task, Environment, and Provider IDs inside request bodies are sent
without local ULID-format validation; Environment values may follow whatever
ID-or-slug convention the service accepts.

## Models and creation

`ReleaseCreate` requires `experiment_id`, a nonempty `environments` list, and
`version`; `task_id` is optional in the model but needed for global creation.
`Release` includes Task, Experiment, Environment, and Provider IDs; version
and status; deployed/retired timestamps and booleans; nested Task,
Experiment, and Environment data; and an optional endpoint.

```python
from guidelight.models import ReleaseCreate

created = task_releases.create(
    ReleaseCreate(
        experiment_id=experiment.id,
        environments=["staging", "production"],
        version="1.0.0",
    )
)
staging_release, production_release = created

global_created = global_releases.create(
    ReleaseCreate(
        task_id=task.id,
        experiment_id=experiment.id,
        environments=["staging"],
        version="1.0.1",
    )
)
```

## Updates and lifecycle actions

`ReleaseUpdate` accepts `provider_id`, `deployed_on`, and `retired_on`.
`ReleasePatch` accepts the same fields but requires at least one non-`None`
value. `ReleaseTest` requires `input`; `ReleaseTestResult` contains
`output_text` and `error`.

```python
from guidelight.models import ReleasePatch, ReleaseTest, ReleaseUpdate

release = global_releases.update(
    staging_release.id,
    ReleaseUpdate(provider_id="<provider-ulid>"),
)

release = global_releases.patch(
    release.id,
    ReleasePatch(provider_id="<replacement-provider-ulid>"),
)

release = global_releases.deploy(release.id)
result = global_releases.test(
    release.id,
    ReleaseTest(input="Extract this receipt."),
)
release = global_releases.retire(release.id)
```

Cloning is a creation action with its own lifecycle:

```python
clones = global_releases.clone(
    release.id,
    environments=["qa", "production"],
)

for clone in clones:
    clone = global_releases.deploy(clone.id)
    # Use or test the clone, then retire it independently.
    clone = global_releases.retire(clone.id)
```

`clone()` returns a list because each destination Environment gets a distinct
Release. A clone is not automatically deployed or coupled to its source:
track, deploy, retire, and delete every returned Release independently.

## ReleaseGenerations manager

```python
release_generations = global_releases.generations(release.id)
```

Its public collection operations are:

- `list(**options) -> Page[Generation]`
- `iterate(**options)` across Release Generation pages

Both accept `page_size`, `offset`, and `order_by`; there are no additional
filters. The same data can be selected globally with
`endeavor.generations.list(release_id=release.id)`.

## Deletion dependencies

Delete Release-associated Generation Comments and Generations first. Retire a
deployed Release before deleting it. Delete all clones separately; deleting
the source does not manage their lifecycle. Delete Releases before their
Experiment and Task.

```python
for generation in release_generations.list():
    endeavor.generations.delete(generation.id)

if release.is_deployed and not release.is_retired:
    release = global_releases.retire(release.id)
global_releases.delete(release.id)
```
