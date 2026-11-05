# Media

[Resource index](README.md) · [Core concepts](../concepts.md) ·
[Executing deployed Tasks](../execution.md)

Media represents file metadata persisted by Endeavor. It is separate from the
binary content: list or search metadata with the Media manager and stream the
file with `download()`.

This resource is also distinct from `ExecutionAttachment`. A deployed Task can
return generated files directly in a multipart response; `run_with_result()`
decodes those files into execution attachments with in-memory `data`. They are
not persisted Media objects, and the immediate execution response does not
provide a Generation ID through which to retrieve Media metadata.

## Manager API

```python
matches = endeavor.media.search("example.png")
media = matches.items[0]

with endeavor.media.download(
    media.id,
    filename=media.name,
) as download:
    download.write_to("generated/" + media.name)
```

The manager supports:

- `list(**options) -> Page[Media]`
- `iterate(**options) -> Iterator[Media]`
- `search(query, **options) -> Page[Media]`
- `update(ref, request=None, **fields) -> Media`
- `delete(ref) -> None`
- `download(ref, filename="download") -> MediaDownload`

`list()` accepts `content_type`, `modality`, and `created_by` filters.
`search()` accepts those filters plus `unknown`; `unknown=True` restricts
results to Media whose content type Endeavor records as unknown.

`MediaDownload` is a context manager. Its `write_to()` method accepts either a
filesystem path or an open binary stream and supports a configurable
`chunk_size`.

The download `filename` must be one nonempty, path-safe component. Absolute
paths, separators, traversal components, query strings, fragments, and
percent-encoded path data are rejected before an authenticated request is
created.

Media metadata can come from
`list()`, `search()`, an update response, or attachment metadata on another
resource such as a Generation. The typed metadata includes the creating
subject in `created_by` and, for converted Media, the source Media ID in
`converted_from`. Either field can be `None` when Endeavor omits it.

## Uploads and API subjects

Direct Media creation and upload are intentionally not exposed in this SDK
phase because Endeavor's standalone Media upload route requires a user
subject.

API-subject callers should import PDF and image inputs through Test Case archive
upload instead. Endeavor creates the associated Media records internally:

```python
with open("fixtures.zip", "rb") as archive:
    result = endeavor.test_cases.upload_archive(
        archive,
        task_id=task_id,
    )
print(result.testcases)
```

Never log credentials or signed download URLs, and do not fetch arbitrary
remote URLs supplied by callers. Use the server-provided `download_url` only
as metadata; use the authenticated Media download operation to retrieve bytes.
