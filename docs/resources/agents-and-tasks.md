# Agents and Tasks

[Resource index](README.md) · [Core concepts](../concepts.md) ·
[Lifecycle](../lifecycle.md)

An Agent is the top-level AI application and owns Tasks. A Task is one
capability of that Agent and is the parent boundary for Experiments, Metrics,
and Releases; Test Cases may reference a Task. An Agent's BAO is embedded
data, not a separately managed resource.

## Agents

Obtain the global manager from a connected `Endeavor`:

```python
agents = endeavor.agents
```

### Manager API

- `list(*, page_size=None, offset=0, order_by=None, **filters) -> Page[Agent]`
  lists Agents. No resource-specific filters are supported.
- `iterate(**options)` yields Agents across list pages.
- `get(ref) -> Agent` gets one Agent.
- `create(request: AgentCreate | None = None, **fields) -> Agent` creates one.
- `update(ref, request: AgentUpdate | None = None, **fields) -> Agent` replaces
  its writable fields.
- `delete(ref) -> None` deletes it.
- `tasks(ref) -> AgentTasks` returns the Agent-scoped Task manager.

For `get`, `update`, `delete`, and `tasks`, `ref` may be an Agent model, ULID,
or slug. Agent create and update requests do not expose a writable `slug`;
the response may contain the server-assigned slug.

`AgentCreate` and `AgentUpdate` require `name` and `description` and optionally
accept `bao: BAOInput`. `BAOInput` requires `objectives` and may contain
`kpis`, `end_users`, and `sponsor`. The `Agent` response includes `id`,
timestamps, `name`, `slug`, `description`, `bao`, `usage`, and `info`.
`AgentInfo` contains optional task, deployed-task, token, and cost aggregates.

```python
from guidelight.models import AgentCreate, AgentUpdate

agent = agents.create(
    AgentCreate(
        name="Receipt Agent",
        description="Extracts structured receipt fields.",
    )
)

agent = agents.update(
    agent.id,
    AgentUpdate(
        name="Receipt Agent",
        description="Extracts and validates receipt fields.",
    ),
)

tasks = agents.tasks(agent)
```

Delete an Agent only after deleting its Tasks. Each Task's Releases,
Experiments, Metrics, Test Cases, Generations, Comments, and Reviews should be
handled first; see [reverse-order cleanup](../lifecycle.md#8-clean-up-in-reverse-dependency-order).

```python
agents.delete(agent.id)
```

## Tasks

Tasks have no global manager. Obtain an `AgentTasks` manager from an Agent:

```python
tasks = endeavor.agents.tasks(agent)  # Agent model, slug, or ULID
```

The manager is permanently scoped to that Agent for `list()` and `create()`.
Methods addressing an existing Task use global Task routes and accept a Task
model, slug, or ULID.

### Manager API

- `list(**options) -> Page[Task]` lists Tasks under the configured Agent.
  Options support `page_size`, `offset`, and `order_by`; there are no
  Task-specific filters.
- `iterate(**options)` yields the Agent's Tasks across list pages.
- `get(ref) -> Task` gets a Task by model, slug, or ULID.
- `create(request: TaskCreate | None = None, **fields) -> Task` creates a Task
  under the configured Agent.
- `update(ref, request: TaskUpdate | None = None, **fields) -> Task` replaces
  writable Task fields.
- `delete(ref) -> None` deletes the Task.
- `experiments(ref) -> Experiments` returns a Task-scoped Experiment manager.
- `test_cases(ref) -> TestCases` returns a Task-scoped Test Case manager.
- `metrics(ref) -> Metrics` returns a Task-scoped Metric manager.
- `releases(ref) -> Releases` returns a Task-scoped Release manager.

`TaskCreate` requires `name` and `description`; it optionally accepts `slug`,
`bao`, and an initial `metrics: list[MetricCreate]`. `TaskUpdate` requires
`name` and `description` and optionally accepts `slug` and `bao`. The `Task`
response includes `id`, timestamps, `agent_id`, `name`, `slug`, `agent`,
`description`, `status`, `bao`, `metrics`, `usage`, and `counts`. `TaskCounts`
reports release, experiment, testcase, and metric counts.

```python
from guidelight.models import TaskCreate, TaskUpdate

task = tasks.create(
    TaskCreate(
        name="Extract Receipt Fields",
        description="Extract merchant, date, and total.",
        slug="extract-receipt",
    )
)

task = tasks.update(
    task.slug,
    TaskUpdate(
        name="Extract and Validate Receipt Fields",
        description="Extract and validate merchant, date, and total.",
        slug="extract-receipt",
    ),
)

experiments = tasks.experiments(task)
test_cases = tasks.test_cases(task)
metrics = tasks.metrics(task)
releases = tasks.releases(task)
```

Delete Task dependents first: Generation and Experiment Comments, Reviews,
Generations, retired Releases, Experiments, Metrics, and associated Test Cases
or versions. Then delete the Task before deleting its Agent.

```python
tasks.delete(task.id)
```
