"""Shared fixtures and identifiers for resource manager tests."""

EXPERIMENT_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
GENERATION_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
RELEASE_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAX"
TEST_CASE_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAY"
METRIC_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAZ"
USER_ID = "01ARZ3NDEKTSV4RRFFQ69G5FB0"
TASK_ID = "01ARZ3NDEKTSV4RRFFQ69G5FB1"
COMMENT_ID_1 = "01ARZ3NDEKTSV4RRFFQ69G5FB2"
COMMENT_ID_2 = "01ARZ3NDEKTSV4RRFFQ69G5FB3"


class FakeClient:
    """Record requests and return queued or default fake responses."""

    def __init__(self, responses=None):
        self.calls = []
        self.responses = list(responses or [])

    def _response(self):
        return self.responses.pop(0) if self.responses else None

    def get(self, *endpoint, query=None):
        self.calls.append(("GET", endpoint, query))
        if self.responses:
            return self._response()
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
        if self.responses:
            return self._response()
        return {
            "id": "01J7ABCDEF0123456789ABCDEFG",
            "name": data["name"],
            "slug": "support-bot",
            "description": data["description"],
        }

    def put(self, data, *endpoint, **options):
        self.calls.append(("PUT", endpoint, data, options))
        if self.responses:
            return self._response()
        return {
            "id": "01J7ABCDEF0123456789ABCDEFG",
            "name": data["name"],
            "slug": "support-bot",
            "description": data["description"],
        }

    def patch(self, data, *endpoint, **options):
        self.calls.append(("PATCH", endpoint, data, options))
        return self._response()

    def delete(self, *endpoint, **options):
        self.calls.append(("DELETE", endpoint, options))
