# Experiments and Generations

[Resource index](README.md) · [Core concepts](../concepts.md) ·
[Lifecycle](../lifecycle.md)

An Experiment belongs to a Task and combines model, prompt, parameter,
capability, and Test Case Version configuration. Its execution produces
Generations. A Generation is an execution result from either an Experiment or
a deployed Release.

## Experiments

Experiment listing and creation require a Task-scoped manager:

```python
tasks = endeavor.agents.tasks(agent)
experiments = tasks.experiments(task)  # Task model, slug, or ULID
```

### Manager API

- `list(**options) -> Page[Experiment]` lists Experiments for the configured
  Task.
- `iterate(**options)` yields Task-scoped Experiments across list pages.
- `get(ref) -> Experiment` gets an Experiment.
- `create(request: ExperimentCreate | None = None, **fields) -> Experiment`
  creates under the configured Task.
- `update(ref, request: ExperimentUpdate | None = None, **fields) ->
  Experiment` performs a full replacement of writable configuration.
- `patch(ref, request: ExperimentPatch | None = None, **fields) -> Experiment`
  partially updates writable fields.
- `delete(ref) -> None` deletes the Experiment.
- `capabilities(ref, capabilities: list[dict]) -> None` replaces its
  capability associations.
- `test_cases(ref) -> TestCases` returns an Experiment-scoped Test Case list
  manager.
- `set_test_cases(ref, version_ids: list[str])` replaces associated Test Case
  Versions and returns the low-level response.
- `comments(ref) -> Comments` returns its Comment manager.
- `reviews(ref) -> Reviews` returns its Review manager.

`list()` and `iterate()` support `page_size`, `offset`, and `order_by`, plus
`task_ids`, `status`, `created_after`, `created_before`, `modified_after`, and
`modified_before`.

`get`, `update`, `patch`, `delete`, `capabilities`, and `test_cases` accept an
Experiment model, slug, or ULID. `set_test_cases`, `comments`, and `reviews`
require a strict Experiment ULID; a slug fails local validation.
`set_test_cases()` takes **Test Case Version IDs**, such as
`test_case.latest.id`, never parent Test Case IDs. The list's body values are
sent as supplied and are not ULID-format-validated locally.

### Models and lifecycle

`ExperimentCreate` has optional `name`, `slug`, `description`, `status`
(`"ready"` only when supplied), context and input/output types and modalities,
`model_id`, `renderer`, `prompts`, `parameters`, and `capabilities`.
`ExperimentUpdate` requires `name`, nonempty input/output modalities,
nonempty output types, a `renderer`, and nonempty `prompts`. Text input also
requires `context_type` and nonempty `input_types`. `ExperimentPatch` makes
the configuration fields optional.

The `Experiment` response additionally includes `id`, timestamps, lifecycle
`status`, input/output schemas, `model_name`, `usage`, and `info`. Status may
be `unknown`, `draft`, `ready`, `active`, `review`, `completed`, `error`, or
`archived`.

Create a draft, associate versions, then fully configure it:

```python
from guidelight.models import ExperimentCreate, ExperimentUpdate

experiment = experiments.create(
    ExperimentCreate(
        name="Receipt extraction baseline",
        description="Evaluates a receipt prompt.",
    )
)

experiments.set_test_cases(
    experiment.id,                 # strict Experiment ULID
    [test_case.latest.id],         # Test Case Version ULID
)

experiment = experiments.update(
    experiment.id,
    ExperimentUpdate(
        name="Receipt extraction baseline",
        description="Configured and ready.",
        status="ready",
        context_type="text/plain",
        input_types=["text/plain"],
        input_modality=["Text"],
        output_types=["application/json"],
        output_modality=["Text"],
        model_id="<model-ulid>",
        renderer="go",
        prompts=[
            {"role": "system", "template": "Extract receipt fields."},
            {"role": "user", "template": "{{ context }}"},
        ],
    ),
)
```

The **first `draft` → `ready` transition executes the Experiment
asynchronously**. There is no `run()` manager method. The update response does
not mean Generation work is complete; poll `get()` until a terminal or
reviewable status and then list Generations. Endeavor's server policy permits
only `name`, `slug`, and `description` changes after an Experiment leaves
draft. `ExperimentPatch` exposes the complete patch schema, so the SDK can
serialize other fields, but the server may reject them for a non-draft
Experiment.

Other actions and metadata updates:

```python
from guidelight.models import ExperimentPatch

experiments.capabilities(
    experiment.id,
    [{"name": "structured-output"}],
)

experiment = experiments.patch(
    experiment.id,
    ExperimentPatch(description="Execution metadata updated."),
)
```

Delete Experiment Comments and Reviews, its Generations, and every Release
that promotes it before deleting the Experiment. Remove associated Test Case
Versions when required by the service.

```python
experiments.delete(experiment.id)
```

## Generations

Obtain the global manager directly:

```python
generations = endeavor.generations
```

Generations intentionally have **no `create()` or `update()` method**. They
are produced by Experiment execution or deployed Release execution.

### Manager API

- `list(*, experiment_id=None, release_id=None, **options) ->
  Page[Generation]` lists Generations; the two filters are mutually exclusive.
- `iterate(**options)` yields Generations across list pages.
- `get(ref) -> Generation` gets one.
- `delete(ref) -> None` deletes one.
- `metrics(ref) -> Page[Metric]` reads its Metric result values.
- `feedback(ref, request=None, **fields) -> GenerationFeedbackResponse`
  submits scores.
- `set_golden(ref, test_case_ids: list[str])` associates golden-example Test
  Cases and returns the low-level response.
- `create_test_case(ref, request=None, **fields) -> TestCase` saves a
  Generation's output or input as a new Test Case associated with one or more
  Tasks.
- `comments(ref) -> Comments` returns its Comment manager.

`list()` and `iterate()` support `page_size`, `offset`, and `order_by`.
`experiment_id` and `release_id` are the only resource-specific filters.
Every method addressing one Generation requires its ULID; slugs fail local
validation. Body values such as filter IDs, Metric IDs in `scores`, and Test
Case IDs in `set_golden()` are sent without local ULID-format validation.

`Generation` includes IDs for its Experiment, Release, previous, and next
Generation; title, error, context, rendered prompt, modalities, output text,
timing, invocation/tool-call counts, token and cost data, attachments, and
golden-example Test Cases. `GenerationFeedback` requires a nonempty
`scores: dict[str, float]` and optionally accepts `generation_id`.
`GenerationFeedbackResponse` includes success, Generation and Review IDs,
status, completion counts, and accepted scores.
`GenerationTestCaseCreate` requires at least one Task ID, optionally accepts a
Test Case name, and uses `from_input=False` by default. Experiment Generations
must use their output because Endeavor rejects `from_input=True` for them.

```python
from guidelight.models import GenerationFeedback, GenerationTestCaseCreate

page = generations.list(experiment_id=experiment.id, page_size=100)
generation = page.items[0]

metric_values = generations.metrics(generation.id)
feedback = generations.feedback(
    generation.id,
    GenerationFeedback(scores={metric.id: 0.9}),
)
generations.set_golden(generation.id, [test_case.id])
saved_test_case = generations.create_test_case(
    generation.id,
    GenerationTestCaseCreate(
        task_ids=[task.id],
        name="Representative output",
    ),
)
generation_comments = generations.comments(generation.id)
```

Delete Generation Comments first. Remove golden-output and golden-example
relationships involving the Generation before deletion. Delete Generations
before their Experiment and Release parents.

```python
generations.delete(generation.id)
```
