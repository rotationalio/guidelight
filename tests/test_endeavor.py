import json
from unittest.mock import Mock

import pytest
from requests import Response

import guidelight.models as model_exports
import guidelight.resources as resource_exports
from guidelight.endeavor import Endeavor
from guidelight.exceptions import InvalidResponse
from guidelight.models.execution import ExecutionResult
from guidelight.resources import (
    Agents,
    Environments,
    Generations,
    GovernancePolicies,
    MediaCollection,
    Models,
    Providers,
    Releases,
)
from guidelight.resources import TestCases as CaseManager


class FakeClient:
    def status(self):
        return {"status": "ok"}


def test_endeavor_exposes_client_and_resource_managers():
    """The high-level entry point exposes every implemented resource manager."""
    client = FakeClient()
    endeavor = Endeavor(client)
    expected_managers = {
        "agents": Agents,
        "environments": Environments,
        "generations": Generations,
        "governance_policies": GovernancePolicies,
        "media": MediaCollection,
        "models": Models,
        "providers": Providers,
        "releases": Releases,
        "test_cases": CaseManager,
    }

    assert endeavor.client is client
    for attribute, manager_type in expected_managers.items():
        assert isinstance(getattr(endeavor, attribute), manager_type)
    assert endeavor.status() == {"status": "ok"}


def test_configuration_models_and_resources_are_publicly_exported():
    """Public modules export all configuration types and managers."""
    expected_models = {
        "Environment",
        "EnvironmentCreate",
        "EnvironmentPatch",
        "EnvironmentUpdate",
        "ExecutionAttachment",
        "ExecutionModel",
        "ExecutionResult",
        "ExecutionUsage",
        "GovernancePolicy",
        "GovernancePolicyCreate",
        "GovernancePolicyPatch",
        "Model",
        "ModelUsage",
        "ModalityName",
        "Provider",
        "ProviderCreate",
        "ProviderCredential",
        "ProviderCredentialCreate",
        "ProviderCredentialPatch",
        "ProviderCredentialUpdate",
        "ProviderPatch",
        "ProviderStatusResponse",
        "ProviderUpdate",
    }
    expected_resources = {
        "Environments",
        "GovernancePolicies",
        "Models",
        "ProviderCredentials",
        "Providers",
    }

    assert expected_models <= set(model_exports.__all__)
    assert expected_resources <= set(resource_exports.__all__)
    assert all(hasattr(model_exports, name) for name in expected_models)
    assert all(hasattr(resource_exports, name) for name in expected_resources)


def test_endeavor_run_delegates_to_client():
    class ExecutionClient(FakeClient):
        def execute(self, *args, **kwargs):
            response = Response()
            response.status_code = 200
            response.headers["Content-Type"] = "text/plain"
            response._content = b"completed"
            self.execution = (args, kwargs)
            return response

    client = ExecutionClient()
    result = Endeavor(client).run(
        "agent",
        "task",
        context={"input": "value"},
        environment="staging",
        version="1.2.3",
    )

    assert result == "completed"
    assert client.execution[0] == ()
    assert client.execution[1]["agent"] == "agent"
    assert client.execution[1]["task"] == "task"
    assert client.execution[1]["environment"] == "staging"
    assert client.execution[1]["version"] == "1.2.3"
    assert client.execution[1]["raw"] is True


def test_endeavor_run_decodes_json_response():
    class ExecutionClient(FakeClient):
        def execute(self, *args, **kwargs):
            response = Response()
            response.status_code = 200
            response.headers["Content-Type"] = "application/json"
            response._content = b'{"answer":42}'
            return response

    result = Endeavor(ExecutionClient()).run("agent", "task")

    assert result == {"answer": 42}


def test_endeavor_run_returns_none_for_no_content_response():
    class ExecutionClient(FakeClient):
        def execute(self, *args, **kwargs):
            return None

    assert Endeavor(ExecutionClient()).run("agent", "task") is None


def test_endeavor_run_forwards_files_environment_and_version():
    class ExecutionClient(FakeClient):
        def execute(self, *args, **kwargs):
            response = Response()
            response.status_code = 200
            response.headers["Content-Type"] = "text/plain"
            response._content = b"completed"
            self.execution = (args, kwargs)
            return response

    client = ExecutionClient()
    files = {"example.pdf": object()}

    result = Endeavor(client).run(
        "document-agent",
        "extract-text",
        context={"instruction": "Extract text."},
        environment="production",
        version="1.2.3",
        files=files,
    )

    assert result == "completed"
    assert client.execution[1]["agent"] == "document-agent"
    assert client.execution[1]["task"] == "extract-text"
    assert client.execution[1]["environment"] == "production"
    assert client.execution[1]["version"] == "1.2.3"
    assert client.execution[1]["files"] is files
    assert client.execution[1]["raw"] is True


def test_endeavor_run_forwards_full_url_and_files():
    class ExecutionClient(FakeClient):
        def execute(self, *args, **kwargs):
            response = Response()
            response.status_code = 200
            response.headers["Content-Type"] = "text/plain"
            response._content = b"completed"
            self.execution = (args, kwargs)
            return response

    client = ExecutionClient()
    files = {"example.pdf": object()}
    deployed_task_url = "https://endeavor.example.com/api/document-agent/extract-text"

    result = Endeavor(client).run(
        deployed_task_url=deployed_task_url,
        context={"instruction": "Extract text."},
        files=files,
    )

    assert result == "completed"
    assert client.execution[1]["agent"] is None
    assert client.execution[1]["task"] is None
    assert client.execution[1]["deployed_task_url"] == deployed_task_url
    assert client.execution[1]["files"] is files
    assert client.execution[1]["raw"] is True


def execution_output(**updates):
    output = {
        "usage": {
            "invocations": 1,
            "tool_calls": 0,
            "input_tokens": 8,
            "output_tokens": 4,
            "total_tokens": 12,
            "api_cost": 0.01,
            "energy_cost": 0.0,
        },
        "model": {
            "slug": "google/gemini-2.5-flash-image",
            "parameters": {"temperature": 0.2},
        },
        "output": "Generated image",
        "mime_type": "text/plain",
        "capabilities": ["image_generation"],
        "started": "2026-11-02T12:00:00Z",
        "finished": "2026-11-02T12:00:01Z",
        "outcome": "succeeded",
        "Attachments": [],
    }
    output.update(updates)
    return output


def multipart_execution_body(payload, attachment=b"png bytes", output_name="output"):
    boundary = "guidelight-test-boundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{output_name}"\r\n'
        "\r\n"
        f"{json.dumps(payload)}\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="generated.png"; '
        'filename="generated.png"\r\n'
        "Content-Type: application/octet-stream\r\n"
        "\r\n"
    ).encode()
    body += attachment
    body += f"\r\n--{boundary}--\r\n".encode("ascii")
    return body, f"multipart/form-data; boundary={boundary}"


def test_endeavor_run_with_result_decodes_execution_output():
    response = Response()
    response.status_code = 200
    response.headers["Content-Type"] = "application/json"
    response._content = json.dumps(execution_output()).encode("utf-8")
    response.close = Mock(wraps=response.close)

    class ExecutionClient(FakeClient):
        def execute(self, *args, **kwargs):
            return response

    result = Endeavor(ExecutionClient()).run_with_result(
        "agent",
        "task",
        context={"prompt": "draw a circle"},
    )

    assert result.output == "Generated image"
    assert result.model.slug == "google/gemini-2.5-flash-image"
    assert result.usage.total_tokens == 12
    assert result.outcome == "succeeded"
    assert result.attachments == []
    assert result.raw_response["mime_type"] == "text/plain"
    response.close.assert_called_once_with()


def test_endeavor_run_decodes_multipart_execution_output_and_closes_response():
    payload = execution_output(
        output={"caption": "Generated image"},
        mime_type="application/json",
        Attachments=[
            {
                "filename": "generated.png",
                "content_type": "image/png",
                "data": "cG5nIGJ5dGVz",
            }
        ],
    )
    body, content_type = multipart_execution_body(payload)
    response = Response()
    response.status_code = 200
    response.headers["Content-Type"] = content_type
    response._content = body
    response.close = Mock(wraps=response.close)

    class ExecutionClient(FakeClient):
        def execute(self, *args, **kwargs):
            return response

    result = Endeavor(ExecutionClient()).run("agent", "task")

    assert isinstance(result, ExecutionResult)
    assert result.output == {"caption": "Generated image"}
    assert result.attachments[0].filename == "generated.png"
    assert result.attachments[0].content_type == "image/png"
    assert result.attachments[0].data == b"png bytes"
    response.close.assert_called_once_with()


def test_endeavor_run_with_result_rejects_unrelated_json():
    class ExecutionClient(FakeClient):
        def execute(self, *args, **kwargs):
            response = Response()
            response.status_code = 200
            response.headers["Content-Type"] = "application/json"
            response._content = b'{"answer":42}'
            return response

    with pytest.raises(InvalidResponse, match="invalid execution output"):
        Endeavor(ExecutionClient()).run_with_result("agent", "task")


def test_endeavor_run_with_result_rejects_malformed_multipart():
    payload = execution_output(
        Attachments=[
            {
                "filename": "generated.png",
                "content_type": "image/png",
                "data": "cG5nIGJ5dGVz",
            }
        ],
    )
    body, content_type = multipart_execution_body(payload, output_name="result")
    response = Response()
    response.status_code = 200
    response.headers["Content-Type"] = content_type
    response._content = body
    response.close = Mock(wraps=response.close)

    class ExecutionClient(FakeClient):
        def execute(self, *args, **kwargs):
            return response

    with pytest.raises(
        InvalidResponse,
        match="first multipart execution part must be named 'output'",
    ):
        Endeavor(ExecutionClient()).run_with_result("agent", "task")

    response.close.assert_called_once_with()
