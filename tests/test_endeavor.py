from requests import Response

import guidelight.models as model_exports
import guidelight.resources as resource_exports
from guidelight.endeavor import Endeavor
from guidelight.resources import (
    Agents,
    Environments,
    Generations,
    GovernancePolicies,
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
        "GovernancePolicy",
        "GovernancePolicyCreate",
        "GovernancePolicyPatch",
        "Model",
        "ModelUsage",
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
