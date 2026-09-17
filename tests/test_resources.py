import pytest

from guidelight.resources import Agents, PageInfo, reference


class FakeClient:
    def __init__(self):
        self.calls = []

    def get(self, *endpoint, query=None):
        self.calls.append(("GET", endpoint, query))
        if endpoint == ("agents",):
            return {
                "page": {"page_size": 25, "offset": 0},
                "agents": [
                    {
                        "id": "01J7ABCDEF0123456789ABCDEFG",
                        "name": "Support Bot",
                        "slug": "support-bot",
                        "description": "Answers questions.",
                    }
                ],
                "provider_id": "provider-1",
            }
        return {
            "id": "01J7ABCDEF0123456789ABCDEFG",
            "name": "Support Bot",
            "slug": "support-bot",
            "description": "Answers questions.",
        }

    def post(self, data, *endpoint, **options):
        self.calls.append(("POST", endpoint, data, options))
        return {
            "id": "01J7ABCDEF0123456789ABCDEFG",
            "name": data["name"],
            "slug": "support-bot",
            "description": data["description"],
        }

    def put(self, data, *endpoint, **options):
        self.calls.append(("PUT", endpoint, data, options))
        return {
            "id": "01J7ABCDEF0123456789ABCDEFG",
            "name": data["name"],
            "slug": "support-bot",
            "description": data["description"],
        }

    def delete(self, *endpoint, **options):
        self.calls.append(("DELETE", endpoint, options))


def test_agents_list_decodes_page_and_metadata():
    client = FakeClient()
    page = Agents(client).list(page_size=25, order_by=["name", "-created"])

    assert page.items[0].name == "Support Bot"
    assert page.page == PageInfo(page_size=25, offset=0)
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
    agents.update(
        agent,
        name="Updated Bot",
        description="An updated bot.",
    )
    agents.delete(agent)

    assert client.calls[0][1] == ("agents", "support-bot")
    assert client.calls[1][1] == ("agents",)
    assert client.calls[2][1] == ("agents", "support-bot")
    assert client.calls[3][1] == ("agents", "support-bot")


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

