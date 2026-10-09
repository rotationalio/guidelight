import pytest

from guidelight.models import AgentCreate, AgentUpdate
from guidelight.resources import Agents, PageInfo, reference

from .shared import FakeClient


def test_agents_list_decodes_page_and_metadata():
    client = FakeClient()
    page = Agents(client).list(page_size=25, order_by=["name", "-created"])

    assert page.items[0].name == "Support Bot"
    assert page.page_info == PageInfo(page_size=25, offset=0)
    assert page.metadata == {"provider_id": "provider-1"}
    assert client.calls[0][2] == {
        "offset": 0,
        "page_size": 25,
        "order_by": ["name", "-created"],
    }


def test_agents_crud_uses_explicit_paths_and_request_fields():
    client = FakeClient()
    agents = Agents(client)

    agent = agents.get("support-bot")
    agents.create(name="New Bot", description="A new bot.")
    agents.update(agent, name="Updated Bot", description="An updated bot.")
    agents.delete(agent)

    assert client.calls[0][1] == ("agents", "support-bot")
    assert client.calls[1][1] == ("agents",)
    assert client.calls[2][1] == (
        "agents",
        "01J7ABCDEF0123456789ABCDEFG",
    )
    assert client.calls[3][1] == (
        "agents",
        "01J7ABCDEF0123456789ABCDEFG",
    )


def test_agent_request_validation_fails_before_request():
    client = FakeClient()
    agents = Agents(client)
    request = AgentCreate(
        name="Support Bot",
        description="Answers questions.",
    )

    with pytest.raises(
        TypeError,
        match="provide either a request object or keyword fields",
    ):
        agents.create(request, name="Another Bot")

    with pytest.raises(TypeError, match="expected AgentCreate"):
        agents.create(
            AgentUpdate(
                name="Support Bot",
                description="Answers questions.",
            )
        )

    with pytest.raises(TypeError, match="invalid AgentCreate fields"):
        agents.create(name="Missing Description")

    assert client.calls == []


def test_agent_tasks_is_explicitly_scoped():
    client = FakeClient()
    tasks = Agents(client).tasks("support-bot")

    assert tasks.collection_path == ("agents", "support-bot", "tasks")


def test_invalid_filters_and_references_fail_before_requests():
    client = FakeClient()
    agents = Agents(client)

    with pytest.raises(TypeError):
        agents.list(unknown=True)
    with pytest.raises(ValueError):
        reference("../agent", allow_slug=True)

    assert client.calls == []
