from datetime import datetime, timezone

from guidelight.models import Agent, AgentCreate, AgentUpdate, BAOInput


def test_agent_response_parses_nested_readonly_fields():
    agent = Agent.from_dict(
        {
            "id": "01J7ABCDEF0123456789ABCDEFG",
            "created": "2026-09-16T12:00:00Z",
            "modified": "2026-09-16T13:00:00+00:00",
            "name": "Support Bot",
            "slug": "support-bot",
            "description": "Answers questions.",
            "bao": {"objectives": "Reduce support time"},
            "usage": {"requests": 4},
            "info": {"task_count": 2},
            "new_server_field": True,
        }
    )

    assert agent.name == "Support Bot"
    assert agent.created == datetime(2026, 9, 16, 12, tzinfo=timezone.utc)
    assert agent.bao.objectives == "Reduce support time"
    assert agent.info.task_count == 2
    assert agent.usage == {"requests": 4}
    assert agent._extra == {"new_server_field": True}


def test_agent_requests_only_serialize_writable_fields():
    bao = BAOInput(objectives="Reduce support time", end_users=["customers"])
    create = AgentCreate(
        name="Support Bot",
        description="Answers questions.",
        bao=bao,
    )
    update = AgentUpdate(name="Updated Bot", description="Updated description.")

    assert create.to_dict() == {
        "name": "Support Bot",
        "description": "Answers questions.",
        "bao": {
            "objectives": "Reduce support time",
            "end_users": ["customers"],
        },
    }
    assert update.to_dict() == {
        "name": "Updated Bot",
        "description": "Updated description.",
    }
