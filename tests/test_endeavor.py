from requests import Response

from guidelight.endeavor import Endeavor
from guidelight.resources import Agents


class FakeClient:
    def status(self):
        return {"status": "ok"}


def test_endeavor_exposes_client_and_agents():
    client = FakeClient()
    endeavor = Endeavor(client)

    assert endeavor.client is client
    assert isinstance(endeavor.agents, Agents)
    assert endeavor.status() == {"status": "ok"}


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
