# Comments and Reviews

[Resource index](README.md) · [Core concepts](../concepts.md) ·
[Lifecycle](../lifecycle.md)

Comments exposed by Guidelight annotate an Experiment. Reviews belong to one
Experiment and track an invited user's evaluation progress. Neither resource
has a global collection manager. Generation Comments require user-subject
claims and are not exposed by the API-key-authenticated SDK.

## Comments

Obtain a parent-scoped manager:

```python
experiment_comments = experiments.comments(experiment.id)
```

A `Comments` manager is permanently scoped to one Experiment. Its parent
constructor requires a strict ULID; Experiment slugs fail local validation.

### Manager API

- `list(**options) -> Page[Comment]` lists Comments under the parent.
- `iterate(**options)` yields the parent's Comments across list pages.
- `create(request=None, **fields) -> Comment` creates under the parent, using
  `CommentCreate`.
- `update(ref, request=None, **fields) -> Comment` updates content, using
  `CommentUpdate`.
- `delete(ref) -> None` deletes the Comment.

`list()` and `iterate()` accept `page_size`, `offset`, and `order_by`; there
are no Comment-specific filters. Comment references passed to `update` and
`delete` are also strict ULIDs. The manager uses the parent-scoped route for
all operations, so use the manager belonging to the Comment's actual parent.

`CommentCreate` requires `content` and optionally accepts a `reply_to`
Comment ID. `CommentUpdate` requires `content`. The `Comment` response
includes `id`, timestamps, `object_url`, rendered and source content,
`reply_to`, user data, and nested replies.

```python
from guidelight.models import CommentCreate, CommentUpdate

comment = experiment_comments.create(
    CommentCreate(content="The output looks correct.")
)

reply = experiment_comments.create(
    CommentCreate(
        content="Confirmed after a second pass.",
        reply_to=comment.id,
    )
)

comment = experiment_comments.update(
    comment.id,
    CommentUpdate(content="The output looks correct after review."),
)

experiment_comments.delete(reply.id)
experiment_comments.delete(comment.id)
```

Delete replies before their parent Comment when the service does not cascade
them. Delete all Experiment Comments before deleting that Experiment.

## Reviews

Obtain the Experiment-scoped manager:

```python
reviews = experiments.reviews(experiment.id)
```

The parent Experiment reference must be a strict ULID. Reviews have no
ordinary `create`, `get`, or `update` operation. Reviewer invitations require
user-subject claims and are not exposed by the API-key-authenticated SDK.

### Manager API

- `list(**options) -> Page[Review]` lists Reviews under the Experiment.
- `iterate(**options)` yields the Experiment's Reviews across list pages.
- `delete(ref) -> None` deletes a Review by strict Review ULID.

`list()` and `iterate()` accept `page_size`, `offset`, and `order_by`; there
are no Review-specific filters.

`Review` includes `id`, timestamps, `experiment_id`, `user_id`, status and
user data, completed and total counts, percent, and a progress string.

```python
for review in reviews.list():
    print(review.user_id, review.percent, review.status)
    reviews.delete(review.id)
```

Delete Reviews before deleting their Experiment. Deleting a Review does not
delete its reviewer user or the Experiment.
