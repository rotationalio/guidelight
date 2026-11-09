"""High-level Endeavor SDK entry point."""

from __future__ import annotations

import json
from collections.abc import Mapping
from email.parser import BytesParser
from email.policy import default
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from .client import Client
from .exceptions import InvalidResponse, UnsupportedResponseType
from .models.execution import ExecutionAttachment, ExecutionResult
from .resources import (
    Agents,
    Environments,
    Generations,
    GovernancePolicies,
    MediaCollection,
    Models,
    Providers,
    Releases,
    TestCases,
)
from .url import URL, parse_content_type


class Endeavor:
    """High-level wrapper over an authenticated low-level Client."""

    def __init__(self, client: Client):
        """Initialize the SDK and expose its top-level resource managers.

        ``agents`` is the entry point for Agent resources and Agent-scoped
        Tasks. ``test_cases``, ``generations``, and ``releases`` provide direct
        access to their global collections. Task-scoped Experiments, Metrics,
        Test Cases, and Releases are reached through an Agent's Task manager.
        ``environments``, ``providers``, ``models``, and
        ``governance_policies``, ``media`` expose the catalog, and
        governance and media resources.
        """
        self._client = client
        self.agents = Agents(client)
        self.environments = Environments(client)
        self.generations = Generations(client)
        self.governance_policies = GovernancePolicies(client)
        self.media = MediaCollection(client)
        self.models = Models(client)
        self.providers = Providers(client)
        self.releases = Releases(client)
        self.test_cases = TestCases(client)

    @property
    def client(self) -> Client:
        """Return the underlying transport for unsupported or advanced routes."""
        return self._client

    def status(self):
        """Return server status information."""
        return self._client.status()

    def run(
        self,
        agent: str | None = None,
        task: str | None = None,
        context: Any = None,
        *,
        deployed_task_url: str | URL | None = None,
        environment: str | None = None,
        version: str | None = None,
        files: Mapping[str, Any] | None = None,
    ) -> Any:
        """Execute a deployed Task and decode its successful response.
        This method is more flexible and allows for more control over decoding the response.
        Use `run_with_result` for a more convenient interface that validates and decodes the response.

        Args:
            agent: Agent ID or slug identifying the deployed Task.
            task: Task ID or slug identifying the deployed Task.
            context: Input context sent to the deployed Task.
            deployed_task_url: Direct URL for the deployed Task endpoint.
            environment: Optional deployment environment selector.
            version: Optional release version selector.
            files: Optional multipart files sent with the execution request.

        Returns:
            The decoded JSON value, plain-text string, typed multipart
            execution result, or ``None`` for an empty successful response.

        Raises:
            UnsupportedResponseType: If the response is neither JSON nor plain
                text.
        """
        response = self._client.execute(
            agent=agent,
            task=task,
            deployed_task_url=deployed_task_url,
            context=context,
            environment=environment,
            version=version,
            files=files,
            raw=True,
        )
        return self._decode_execution_response(response)

    @staticmethod
    def _decode_execution_response(response):
        """Decode a raw successful execution response using its content type.

        JSON responses are returned as decoded Python values, plain-text
        responses are returned as strings, and an absent response is returned
        as ``None``.

        Raises:
            UnsupportedResponseType: If the response content type is not
                supported by the high-level SDK.
        """
        if response is None:
            return None

        mime, _ = parse_content_type(response.headers.get("Content-Type", ""))
        try:
            if mime == "text/plain":
                return response.text
            if mime == "application/json":
                return response.json()
            if mime == "multipart/form-data":
                return Endeavor._decode_typed_execution_response(response)
            raise UnsupportedResponseType(mime)
        finally:
            response.close()

    def run_with_result(
        self,
        agent: str | None = None,
        task: str | None = None,
        context: Any = None,
        *,
        deployed_task_url: str | URL | None = None,
        environment: str | None = None,
        version: str | None = None,
        files: Mapping[str, Any] | None = None,
    ) -> ExecutionResult | None:
        """Execute a deployed Task and decode its typed execution output.

        Args:
            agent: Agent ID or slug identifying the deployed Task.
            task: Task ID or slug identifying the deployed Task.
            context: Input context sent to the deployed Task.
            deployed_task_url: Direct URL for the deployed Task endpoint.
            environment: Optional deployment environment selector.
            version: Optional release version selector.
            files: Optional multipart files sent with the execution request.

        Returns:
            The typed execution result, or ``None`` for an empty successful
            response.

        Raises:
            InvalidResponse: If the execution response is malformed.
            UnsupportedResponseType: If the response is neither JSON nor
                multipart form data.
        """
        response = self._client.execute(
            agent=agent,
            task=task,
            deployed_task_url=deployed_task_url,
            context=context,
            environment=environment,
            version=version,
            files=files,
            raw=True,
        )
        if response is None:
            return None

        mime, _ = parse_content_type(response.headers.get("Content-Type", ""))
        try:
            if mime not in {"application/json", "multipart/form-data"}:
                raise UnsupportedResponseType(mime)
            return self._decode_typed_execution_response(response)
        finally:
            response.close()

    @staticmethod
    def _decode_typed_execution_response(response) -> ExecutionResult:
        """Decode a typed JSON or multipart execution response."""
        mime, _ = parse_content_type(response.headers.get("Content-Type", ""))

        try:
            if mime == "application/json":
                payload = response.json()
                attachments = None
            elif mime == "multipart/form-data":
                payload, attachments = Endeavor._decode_execution_multipart(response)
            else:
                raise UnsupportedResponseType(mime)

            if not isinstance(payload, dict):
                raise InvalidResponse("execution output must be a JSON object")

            model_payload = dict(payload)
            if attachments is not None:
                model_payload.pop("Attachments", None)
                model_payload.pop("attachments", None)
                model_payload["attachments"] = attachments
            model_payload["raw_response"] = payload
            return ExecutionResult.model_validate(model_payload)
        except InvalidResponse:
            raise
        except (PydanticValidationError, TypeError, ValueError) as exc:
            raise InvalidResponse(f"invalid execution output: {exc}") from exc

    @staticmethod
    def _decode_execution_multipart(
        response,
    ) -> tuple[dict[str, Any], list[ExecutionAttachment]]:
        """Decode execution output metadata and generated file parts."""
        content_type = response.headers.get("Content-Type", "")
        message = BytesParser(policy=default).parsebytes(
            (f"Content-Type: {content_type}\r\n" "MIME-Version: 1.0\r\n\r\n").encode(
                "ascii"
            )
            + response.content
        )
        if not message.is_multipart():
            raise InvalidResponse("invalid multipart execution response")

        parts = list(message.iter_parts())
        if not parts:
            raise InvalidResponse("multipart execution response has no parts")

        output_part = parts[0]
        output_name = output_part.get_param(
            "name",
            header="content-disposition",
        )
        if output_name != "output":
            raise InvalidResponse(
                "first multipart execution part must be named 'output'"
            )

        output_data = output_part.get_payload(decode=True) or b""
        try:
            payload = json.loads(
                output_data.decode(output_part.get_content_charset() or "utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidResponse("multipart output part is not valid JSON") from exc

        if not isinstance(payload, dict):
            raise InvalidResponse("multipart output part must be a JSON object")

        metadata = payload.get("Attachments", payload.get("attachments", [])) or []
        if not isinstance(metadata, list):
            raise InvalidResponse("execution attachment metadata must be a list")

        file_parts = parts[1:]
        if len(metadata) != len(file_parts):
            raise InvalidResponse(
                "execution attachment metadata does not match multipart files"
            )

        attachments = []
        for index, (part, item) in enumerate(zip(file_parts, metadata)):
            if not isinstance(item, dict):
                raise InvalidResponse(
                    f"execution attachment {index} metadata must be an object"
                )

            filename = part.get_filename()
            if not filename:
                raise InvalidResponse(f"execution attachment {index} has no filename")
            if item.get("filename") not in {None, filename}:
                raise InvalidResponse(
                    f"execution attachment {index} filename does not match metadata"
                )

            attachment_data = dict(item)
            attachment_data.pop("data", None)
            attachment_data["filename"] = filename
            attachment_data["content_type"] = (
                attachment_data.get("content_type") or part.get_content_type() or ""
            )
            attachment_data["data"] = part.get_payload(decode=True) or b""
            attachments.append(ExecutionAttachment.model_validate(attachment_data))

        return payload, attachments
