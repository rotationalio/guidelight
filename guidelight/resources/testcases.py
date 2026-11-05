from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO

from ..exceptions import InvalidResponse
from ..media import MediaDownload
from ..models import (
    PromptRenderer,
    PromptRenderRequest,
    PromptTemplate,
    RenderedPrompt,
    TestCase,
    TestCaseArchiveRequest,
    TestCaseArchiveUploadResponse,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseVersion,
)
from ..url import parse_content_type
from .base import (
    CollectionManager,
    Page,
    ResourceManager,
    decode_page,
    reference,
    request_object,
    resolve_resource_ref,
)


class TestCases(CollectionManager[TestCase]):
    """Manager for the Test Case resource."""

    collection_path = ("testcases",)
    valid_filters = frozenset(
        {
            "agent_id",
            "task_id",
            "experiment_id",
            "context_type",
            "input_modality",
        }
    )

    def __init__(self, client, *, agent=None, task=None, experiment=None):
        """Create a Test Case manager with at most one parent scope."""
        super().__init__(client)
        values = [agent, task, experiment]
        if sum(value is not None for value in values) > 1:
            raise ValueError("only one Test Case parent may be selected")
        if agent is not None:
            self.parent = ("agents", resolve_resource_ref(agent))
        elif task is not None:
            self.parent = ("tasks", resolve_resource_ref(task))
        elif experiment is not None:
            self.parent = ("experiments", resolve_resource_ref(experiment))
        else:
            self.parent = None

    def list(
        self,
        *,
        page_size: int | None = None,
        offset: int = 0,
        order_by: str | list[str] | None = None,
        **filters,
    ) -> Page[TestCase]:
        """List Test Cases using supported filters and pagination options."""
        query = self._query(
            page_size=page_size,
            offset=offset,
            order_by=order_by,
            filters=filters,
        )
        path = self.parent + ("testcases",) if self.parent else self.collection_path
        body = self.client.get(*path, query=query)
        return decode_page(body, key="testcases", model=TestCase)

    def __iter__(self):
        """Iterate over Test Cases using default list options."""
        return self.iterate()

    def get(self, ref: Any) -> TestCase:
        """Retrieve a Test Case by ID or supported reference."""
        return TestCase.from_dict(self.client.get("testcases", reference(ref)))

    def create(self, request=None, **fields) -> TestCase:
        """Create a Test Case in the configured collection."""
        request = request_object(TestCaseCreate, request, fields)
        return TestCase.from_dict(
            self.client.post(request.to_dict(), *self.collection_path)
        )

    def update(self, ref, request=None, **fields) -> TestCase:
        """Update a Test Case by ID or supported reference."""
        request = request_object(TestCaseUpdate, request, fields)
        return TestCase.from_dict(
            self.client.put(request.to_dict(), "testcases", reference(ref))
        )

    def delete(self, ref) -> None:
        """Delete a Test Case by ID or supported reference."""
        self.client.delete("testcases", reference(ref))

    def set_golden(self, ref, generation_id: str) -> TestCase:
        """Set the Generation used as the Test Case golden example."""
        test_case_ref = reference(ref)
        body = self.client.put(
            {"generation_id": generation_id},
            "testcases",
            test_case_ref,
            "golden",
        )
        if body is None:
            return self.get(test_case_ref)
        return TestCase.from_dict(body)

    def versions(self, ref) -> TestCaseVersions:
        """Return a version manager scoped to a Test Case."""
        return TestCaseVersions(self.client, ref)

    def download_archive(
        self,
        destination: str | Path | BinaryIO,
        request=None,
        **fields: Any,
    ) -> int:
        """Download matching Test Cases as a ZIP archive.

        Args:
            destination: Filesystem path or writable binary stream receiving
                the archive.
            request: Optional pre-built archive request model.
            **fields: Exactly one archive selector: ``agent``, ``task``,
                ``experiment``, or ``testcases``.

        Returns:
            The number of bytes written to ``destination``.
        """
        request = request_object(TestCaseArchiveRequest, request, fields)
        response = self.client.post(
            None,
            "testcases",
            "download",
            query=request.to_dict(),
            stream=True,
            raw=True,
        )
        with MediaDownload(response) as download:
            content_type, _ = parse_content_type(download.content_type)
            if content_type != "application/zip":
                raise InvalidResponse(
                    "test case archive response must be application/zip"
                )
            return download.write_to(destination)

    def upload_archive(
        self,
        archive,
        *,
        task_id: str,
    ) -> TestCaseArchiveUploadResponse:
        """Upload a Test Case ZIP archive for a Task.

        Args:
            archive: An open binary file or binary stream containing the ZIP
                archive.
            task_id: Task ID to associate with every imported Test Case.

        Returns:
            The server response containing the number of imported Test Cases.
        """
        data = {"task_id": task_id}
        body = self.client.post(
            data,
            "testcases",
            "upload",
            files={
                "file": (
                    getattr(archive, "name", "testcases.zip"),
                    archive,
                    "application/zip",
                )
            },
        )
        return TestCaseArchiveUploadResponse.from_dict(body)

    def render(
        self,
        test_case: str | TestCase,
        *,
        renderer: PromptRenderer,
        prompts: list[PromptTemplate],
    ) -> RenderedPrompt:
        """Render the latest Test Case version's prompt.

        Args:
            test_case: Test Case ID or response model.
            renderer: Renderer name used to compile the prompt.
            prompts: Prompt templates to render with the Test Case context.

        Returns:
            The rendered messages or template error returned by Endeavor.
            Endeavor returns HTTP 200 when rendering fails, so callers must
            check ``result.error`` before using ``result.messages``.
        """
        request = PromptRenderRequest(renderer=renderer, prompts=prompts)
        return RenderedPrompt.from_dict(
            self.client.post(
                request.to_dict(),
                "testcases",
                reference(test_case),
                "render",
            )
        )


class TestCaseVersions(ResourceManager):
    """Manager for versions belonging to one Test Case."""

    def __init__(self, client, test_case: str):
        """Create a Test Case version manager."""
        super().__init__(client)
        self.test_case = reference(test_case)

    def get(self, version: int) -> TestCaseVersion:
        """Retrieve a specific Test Case version."""
        body = self.client.get("testcases", self.test_case, "versions", str(version))
        return TestCaseVersion.from_dict(body)

    def render(
        self,
        version: int,
        *,
        renderer: PromptRenderer,
        prompts: list[PromptTemplate],
    ) -> RenderedPrompt:
        """Render a specific Test Case version's prompt.

        Args:
            version: Numeric Test Case version to use as prompt context.
            renderer: Renderer name used to compile the prompt.
            prompts: Prompt templates to render with the version's context.

        Returns:
            The rendered messages or template error returned by Endeavor.
            Endeavor returns HTTP 200 when rendering fails, so callers must
            check ``result.error`` before using ``result.messages``.
        """
        request = PromptRenderRequest(renderer=renderer, prompts=prompts)
        return RenderedPrompt.from_dict(
            self.client.post(
                request.to_dict(),
                "testcases",
                self.test_case,
                "versions",
                str(version),
                "render",
            )
        )

    def delete(self, version: int) -> None:
        """Delete a specific Test Case version."""
        self.client.delete("testcases", self.test_case, "versions", str(version))
