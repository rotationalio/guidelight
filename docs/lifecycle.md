# Resource lifecycle

[Documentation home](README.md) · [Getting started](getting-started.md) ·
[Concepts](concepts.md) · [Execution](execution.md)

This guide shows the normal dependency order for one fictional text Task. The
snippets are illustrative and make network calls if run; replace all
placeholders and names before using them with an Endeavor service.

Before starting, obtain the IDs of an existing Model and Environment. An
optional Provider is needed only for provider-specific Release metadata.

## 1. Create an Agent and Task

```python
import guidelight as gdl
from guidelight.models import AgentCreate, TaskCreate

endeavor = gdl.connect()

agent = endeavor.agents.create(
    AgentCreate(
        name="Northwind Triage",
        description="Classifies fictional customer requests.",
    )
)

tasks = endeavor.agents.tasks(agent)
task = tasks.create(
    TaskCreate(
        name="Classify Request",
        description="Assigns one fictional support category.",
    )
)
```

The `tasks` manager remains scoped to this Agent. Task child managers can
accept the Task model, its slug, or its ULID.

## 2. Create Task Test Cases

Test Cases use the global create route. Set `task_id` explicitly even if you
obtained a Task-scoped Test Case manager:

```python
from guidelight.models import TestCaseCreate

test_case = endeavor.test_cases.create(
    TestCaseCreate(
        title="Example delivery question",
        description="A fictional message used for evaluation.",
        context="When would my example order arrive?",
        context_type="text/plain",
        input_modality="Text",
        task_id=task.id,
    )
)
```

Each Test Case is a logical container. Experiments use immutable Test Case
Version IDs, so retain `test_case.latest.id`, not `test_case.id`. If `latest`
is absent in a create response, retrieve the Test Case again before continuing.

## 3. Create a draft Experiment and associate versions

Create the Experiment through its Task-scoped manager:

```python
from guidelight.models import ExperimentCreate

experiments = tasks.experiments(task)
experiment = experiments.create(
    ExperimentCreate(
        name="Northwind triage baseline",
        description="Evaluates the initial fictional triage prompt.",
    )
)

experiments.set_test_cases(
    experiment.id,
    [test_case.latest.id],
)
```

`set_test_cases()` replaces the association set. Both the Experiment reference
and every associated value must be ULIDs; the values are Test Case Version
ULIDs.

## 4. Configure the draft and start execution

There is no `Experiments.run()` method. A full update that changes the first
draft to `status="ready"` is the execution action:

```python
from guidelight.models import ExperimentUpdate

experiment = experiments.update(
    experiment.id,
    ExperimentUpdate(
        name="Northwind triage baseline",
        description="Configured and ready for evaluation.",
        status="ready",
        context_type="text/plain",
        input_types=["text/plain"],
        input_modality=["Text"],
        output_types=["application/json"],
        output_modality=["Text"],
        model_id="<model-ulid>",
        renderer="go",
        prompts=[
            {
                "role": "system",
                "template": "Return one support category as JSON.",
            },
            {
                "role": "user",
                "template": "{{ context }}",
            },
        ],
        parameters={"temperature": 0},
    ),
)
```

The transition validates configuration and asynchronously queues execution.
Poll the Experiment instead of assuming the update response means all
Generations are complete:

```python
import time

while True:
    experiment = experiments.get(experiment.id)
    if experiment.status in {"review", "completed"}:
        break
    if experiment.status in {"error", "archived"}:
        raise RuntimeError(f"Experiment ended as {experiment.status}")
    time.sleep(2)
```

Choose a timeout and backoff appropriate for your application. `ready` and
`active` may be observed while work is in progress. Once an Experiment is no
longer a draft, Endeavor server policy permits only its name, slug, and
description to be changed. `ExperimentPatch` can serialize other fields, but
the server may reject them for a non-draft Experiment.

## 5. Inspect Generations

Experiment execution creates Generations asynchronously:

```python
generation_page = endeavor.generations.list(
    experiment_id=experiment.id,
    page_size=100,
)

for generation in generation_page:
    print(generation.id)
```

Generations have no create or ordinary update operation. Their action methods
support feedback, golden-example associations, Metrics, and Comments. See
[Core concepts](concepts.md#resource-graph) for those relationships.

## 6. Create and deploy a Release

Promote the successful Experiment through the Task-scoped Release manager:

```python
from guidelight.models import ReleaseCreate

releases = tasks.releases(task)
created = releases.create(
    ReleaseCreate(
        experiment_id=experiment.id,
        environments=["staging"],
        version="1.0.0",
    )
)

release = created[0]
release = releases.deploy(release.id)
```

`create()` returns a list because one request may target multiple
Environments, producing one Release per Environment. Global
`endeavor.releases.create()` is also available, but its `ReleaseCreate` must
include `task_id`.

An optional release-scoped smoke test returns a `ReleaseTestResult`:

```python
from guidelight.models import ReleaseTest

smoke = releases.test(
    release.id,
    ReleaseTest(input="Classify this fictional delivery question."),
)

if smoke.error:
    raise RuntimeError(smoke.error)
```

This is distinct from the deployed endpoint call described next; see
[`Release.test()` is different](execution.md#releasetest-is-different).

## 7. Run the deployed Task

Call the deployed Release through its Agent, Task, Environment, and Version
selectors:

```python
result = endeavor.run(
    agent.slug or agent.id,
    task.slug or task.id,
    context={"message": "When would my example order arrive?"},
    environment="staging",
    version=release.version,
)
```

This call is synchronous from the caller's perspective and may produce a
Release-associated Generation. See [Executing deployed Tasks](execution.md)
for files, complete URLs, origin restrictions, and response decoding.

## 8. Clean up in reverse dependency order

Remove dependents before parents. A comprehensive cleanup follows this order:

1. Generation Comments.
2. Experiment Comments and Reviews.
3. Generations created by Experiments or deployed Releases.
4. Retire deployed Releases, then delete Releases.
5. Delete Experiments.
6. Delete Metrics, if created.
7. Delete Test Cases or individual Test Case Versions.
8. Delete Tasks.
9. Delete the Agent last.

For the minimal resources above, which did not create Comments or Reviews:

```python
for generation in endeavor.generations.list(experiment_id=experiment.id):
    endeavor.generations.delete(generation.id)

if release.is_deployed and not release.is_retired:
    release = releases.retire(release.id)
releases.delete(release.id)

experiments.delete(experiment.id)
endeavor.test_cases.delete(test_case.id)
tasks.delete(task.id)
endeavor.agents.delete(agent.id)
```

Production cleanup code should attempt each deletion independently and record
failures so one error does not prevent later resources from being considered.
Also list Release-associated Generations with
`releases.generations(release.id)` before deleting the Release.

