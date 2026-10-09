# Test Cases and Test Case Versions

[Resource index](README.md) · [Core concepts](../concepts.md) ·
[Lifecycle](../lifecycle.md)

A Test Case is a logical evaluation input. Its Test Case Versions are the
immutable revisions associated with Experiments. A Generation may be selected
as a Test Case's golden output.

## Obtaining a manager

```python
from guidelight.resources import TestCases

global_test_cases = endeavor.test_cases
task_test_cases = endeavor.agents.tasks(agent).test_cases(task)
experiment_test_cases = experiments.test_cases(experiment)
agent_test_cases = TestCases(endeavor.client, agent=agent)
```

Only one of `agent`, `task`, or `experiment` may scope a `TestCases` manager.
The scope affects **only `list()`**. In particular, `create()` always posts to
the global Test Case route. Include `task_id` or `experiment_id` in
`TestCaseCreate` to establish the intended relationship.

## TestCases manager API

- `list(**options) -> Page[TestCase]` lists the global collection or the
  configured Agent, Task, or Experiment collection.
- `iterate(**options)` yields Test Cases across list pages.
- `get(ref) -> TestCase` gets one Test Case.
- `create(request=None, **fields) -> TestCase` creates through the global
  collection, using `TestCaseCreate`.
- `update(ref, request=None, **fields) -> TestCase` updates through the global
  route, using `TestCaseUpdate`; changed input may produce a new version.
- `delete(ref) -> None` deletes the Test Case.
- `set_golden(ref, generation_id: str) -> TestCase` chooses the Generation
  used as this Test Case's golden output.
- `versions(ref) -> TestCaseVersions` returns its version manager.

`list()` and `iterate()` accept `page_size`, `offset`, and `order_by`, plus
`agent_id`, `task_id`, `experiment_id`, `context_type`, and `input_modality`
filters.

References to a specific Test Case are ULID-only for `get`, `update`, `delete`,
`set_golden`, and `versions`; Test Case slugs raise `ValueError` locally.
Agent, Task, and Experiment references used only to construct a list scope may
be models, ULIDs, or slugs. Pass a Generation ID—not a slug—as
`generation_id`; body IDs are not format-validated by this SDK before sending.

## Models and examples

`TestCaseCreate` requires `title`. Important optional fields are `description`,
`context`, `context_json`, `context_type`, `input_modality`, attachment IDs,
`task_id`, and `experiment_id`. The SDK permits both context fields to be
omitted, although a particular Endeavor workflow may require an input.
`TestCaseUpdate` has the same input fields except the relationship IDs and
requires `title`.

`TestCase` includes `id`, timestamps, `title`, `description`,
`golden_example`, `versions`, `latest`, `selected`, and `has_golden`.
`latest` is a `TestCaseVersion`, while `versions` contains
`TestCaseVersionURL` entries.

```python
from guidelight.models import TestCaseCreate, TestCaseUpdate

test_case = task_test_cases.create(
    TestCaseCreate(
        title="Coffee shop receipt",
        description="A text evaluation input.",
        context="Coffee Shop\nTotal: $12.50",
        context_type="text/plain",
        input_modality="Text",
        task_id=task.id,  # required relationship despite manager scope
    )
)

test_case = global_test_cases.update(
    test_case.id,
    TestCaseUpdate(
        title="Coffee shop receipt",
        description="A revised input.",
        context="Coffee Shop\nTax: $1.00\nTotal: $12.50",
        context_type="text/plain",
        input_modality="Text",
    ),
)

test_case = global_test_cases.set_golden(
    test_case.id,
    generation.id,
)
```

## TestCaseVersions manager

Obtain it from a strict Test Case ULID:

```python
versions = global_test_cases.versions(test_case.id)
```

Its public operations are:

- `get(version: int) -> TestCaseVersion`
- `delete(version: int) -> None`

It has no `list()` method, so inherited `iterate()` is not applicable.
`TestCaseVersion` includes `id`, numeric `version`, `context`,
`context_type`, `input_modality`, `created`, `selected`, and `attachments`.
Each `TestCaseAttachment` includes its ID, name, description, URL, content
type, and creation time.

```python
version_one = versions.get(1)
versions.delete(1)
```

Experiments associate **Test Case Version IDs**, normally
`test_case.latest.id`, not the parent `test_case.id`:

```python
experiments.set_test_cases(experiment.id, [test_case.latest.id])
```

## Deletion dependencies

Before deleting a version, remove it from any Experiment association set.
Before deleting a Test Case, remove Experiment associations and any
Generation golden-example relationships that depend on it. If the Test Case
uses a Generation as its golden output, clear or delete that relationship
before deleting the Generation. Delete Test Cases before their Task and Agent
parents.

```python
global_test_cases.delete(test_case.id)
```
