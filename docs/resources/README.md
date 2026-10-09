# Resource reference

Use this section for exact manager methods, model fields, scopes, reference
rules, actions, and deletion dependencies. For the shared resource graph,
pagination behavior, and request-model conventions, read
[Core concepts](../concepts.md). For an end-to-end creation, execution, and
cleanup sequence, read [Resource lifecycle](../lifecycle.md).

## Resources

- [Agents and Tasks](agents-and-tasks.md)
- [Test Cases and Test Case Versions](testcases.md)
- [Experiments and Generations](experiments-and-generations.md)
- [Metrics](metrics.md)
- [Releases](releases.md)
- [Comments and Reviews](comments-and-reviews.md)

## Related guides

- [Documentation home](../README.md)
- [Getting started](../getting-started.md)
- [Core concepts](../concepts.md)
- [Executing deployed Tasks](../execution.md)
- [Resource lifecycle](../lifecycle.md)

All managers expose `client`. Collection managers that implement `list()` can
use inherited `iterate(**options)` to yield models across successive
offset-based pages. `TestCaseVersions` is not a collection manager and does not
support `iterate()`. Collection `list()` methods return `Page[Resource]`.

Methods that accept `request=None, **fields` take either a typed request object
or keyword fields, never both; supplying both raises `TypeError`.
