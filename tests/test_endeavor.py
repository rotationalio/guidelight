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
