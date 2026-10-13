# Metrics

[Resource index](README.md) · [Core concepts](../concepts.md) ·
[Lifecycle](../lifecycle.md)

A Metric belongs to a Task and defines how that Task's Generations can be
scored. Generation-specific Metric values are read through the Generation
manager.

## Obtaining a manager

Metrics always require a Task scope:

```python
tasks = endeavor.agents.tasks(agent)
metrics = tasks.metrics(task)  # Task model, slug, or ULID
```

The scope determines the collection used by `list()` and `create()`.

## Manager API

- `list(**options) -> Page[Metric]` lists Metrics under the configured Task.
- `iterate(**options)` yields the Task's Metrics across list pages.
- `create(request=None, **fields) -> Metric` creates a Metric under the Task,
  using `MetricCreate`.
- `get(ref) -> Metric` gets one Metric.
- `update(ref, request=None, **fields) -> Metric` replaces writable fields,
  using `MetricUpdate`.
- `delete(ref) -> None` deletes the Metric.

`list()` and `iterate()` accept `page_size`, `offset`, and `order_by`; there
are no Metric-specific filters. `get`, `update`, and `delete` accept a Metric
model, slug, or ULID.

## Models and examples

`MetricCreate` and `MetricUpdate` require `name` and a nonempty `scoring`
string. Both also accept `description`, `slug`, `widget`, option objects,
`max_score`, `min_score`, and `step`. `Metric` returns those fields plus `id`,
timestamps, `icon`, typed `MetricOption` values, `system`, and an optional
Generation-specific `value`.

```python
from guidelight.models import MetricCreate, MetricUpdate

metric = metrics.create(
    MetricCreate(
        name="Accuracy",
        description="Fraction of fields that match.",
        slug="accuracy",
        scoring="numeric",
        min_score=0,
        max_score=1,
        step=0.1,
    )
)

metric = metrics.update(
    metric.slug,
    MetricUpdate(
        name="Field Accuracy",
        description="Fraction of expected fields that match.",
        slug="accuracy",
        scoring="numeric",
        min_score=0,
        max_score=1,
        step=0.05,
    ),
)

values = endeavor.generations.metrics(generation.id)
feedback = endeavor.generations.feedback(
    generation.id,
    scores={metric.id: 0.95},
)
```

There are no Metric-specific action methods. Feedback submission is a
Generation action and returns `GenerationFeedbackResponse`.

## Deletion dependencies

Remove or no longer depend on Generation feedback, Review scoring, and
Experiment evaluation data that references the Metric before deleting it.
Delete Metrics before their Task. The SDK exposes `delete()` for system and
non-system responses alike; whether the service permits deletion of a
particular `system=True` Metric is server-defined.

```python
metrics.delete(metric.id)
```
