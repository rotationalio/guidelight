import pytest

from guidelight.resources import (
    Agents,
    Comments,
    Environments,
    Generations,
    GovernancePolicies,
    Metrics,
    Models,
    ProviderCredentials,
    Providers,
    ReleaseGenerations,
    Releases,
    Reviews,
    Tasks,
)
from guidelight.resources.base import (
    CollectionManager,
    Page,
    PageInfo,
    ResourceManager,
)
from guidelight.resources.experiments import Experiments
from guidelight.resources.testcases import TestCases as CaseManager
from guidelight.resources.testcases import TestCaseVersions as CaseVersionManager

from .shared import (
    EXPERIMENT_ID,
    PROVIDER_ID,
    RELEASE_ID,
    TASK_ID,
    TEST_CASE_ID,
)


class PagedManager(CollectionManager[int]):
    """Collection manager used to exercise shared pagination behavior."""

    def __init__(self, pages):
        super().__init__(client=object())
        self.pages = iter(pages)
        self.queries = []

    def list(self, **options):
        self.queries.append(options)
        return next(self.pages)


class NonCollectionManager(ResourceManager):
    """Manager representing a resource without a list route."""


def test_collection_manager_iterates_multiple_pages():
    manager = PagedManager(
        [
            Page([1, 2], PageInfo(page_size=2, offset=0)),
            Page([3, 4], PageInfo(page_size=2, offset=2)),
            Page([5], PageInfo(page_size=2, offset=4)),
        ]
    )

    assert list(manager.iterate(page_size=2)) == [1, 2, 3, 4, 5]
    assert [query["offset"] for query in manager.queries] == [0, 2, 4]


def test_collection_manager_stops_at_an_empty_first_page():
    manager = PagedManager([Page([], PageInfo(page_size=2, offset=0))])

    assert list(manager.iterate(page_size=2)) == []
    assert manager.queries == [{"page_size": 2, "offset": 0}]


def test_collection_manager_stops_at_an_empty_page():
    manager = PagedManager(
        [
            Page([1], PageInfo(page_size=2, offset=0)),
            Page([], PageInfo(page_size=2, offset=1)),
        ]
    )

    assert list(manager.iterate(page_size=2)) == [1]


def test_collection_manager_preserves_filters_and_initial_offset():
    manager = PagedManager([Page([1], PageInfo(page_size=10, offset=25))])

    assert list(manager.iterate(page_size=10, offset=25, active=True)) == [1]
    assert manager.queries == [{"page_size": 10, "offset": 25, "active": True}]


def test_non_collection_manager_does_not_expose_iteration():
    manager = NonCollectionManager(client=object())

    assert not hasattr(manager, "iterate")


@pytest.mark.parametrize(
    "manager_factory",
    [
        lambda client: Agents(client),
        lambda client: Tasks(client, "agent"),
        lambda client: CaseManager(client),
        lambda client: Experiments(client, task=TASK_ID),
        lambda client: Generations(client),
        lambda client: Metrics(client, TASK_ID),
        lambda client: Releases(client),
        lambda client: ReleaseGenerations(client, RELEASE_ID),
        lambda client: Comments(client, "experiments", EXPERIMENT_ID),
        lambda client: Reviews(client, EXPERIMENT_ID),
        lambda client: Environments(client),
        lambda client: Providers(client),
        lambda client: ProviderCredentials(client, PROVIDER_ID),
        lambda client: Models(client),
        lambda client: GovernancePolicies(client),
    ],
)
def test_every_listable_manager_inherits_collection_manager(manager_factory):
    """Every manager with a list route shares collection pagination behavior."""
    assert isinstance(manager_factory(object()), CollectionManager)


def test_test_case_versions_do_not_expose_collection_iteration():
    """Version detail routes do not advertise unsupported collection behavior."""
    manager = CaseVersionManager(object(), TEST_CASE_ID)

    assert not isinstance(manager, CollectionManager)
    assert not hasattr(manager, "iterate")
    with pytest.raises(TypeError):
        iter(manager)


def test_collection_manager_does_not_implicitly_expose_python_iteration():
    manager = PagedManager([])

    with pytest.raises(TypeError):
        iter(manager)


@pytest.mark.parametrize(
    "manager_factory",
    [
        lambda client: Agents(client),
        lambda client: Tasks(client, "agent"),
        lambda client: CaseManager(client),
        lambda client: Generations(client),
        lambda client: Metrics(client, TASK_ID),
        lambda client: Releases(client),
        lambda client: ReleaseGenerations(client, RELEASE_ID),
        lambda client: Comments(client, "experiments", EXPERIMENT_ID),
        lambda client: Reviews(client, EXPERIMENT_ID),
        lambda client: Environments(client),
        lambda client: Providers(client),
        lambda client: ProviderCredentials(client, PROVIDER_ID),
        lambda client: Models(client),
        lambda client: GovernancePolicies(client),
    ],
)
def test_managers_with_valid_default_lists_expose_python_iteration(
    manager_factory,
):
    manager = manager_factory(object())

    assert iter(manager) is not None


def test_unscoped_experiments_do_not_expose_python_iteration():
    manager = Experiments(object())

    with pytest.raises(TypeError):
        iter(manager)


@pytest.mark.parametrize(
    ("manager_factory", "key"),
    [
        (lambda client: Environments(client), "environments"),
        (lambda client: Providers(client), "providers"),
        (
            lambda client: ProviderCredentials(client, PROVIDER_ID),
            "credentials",
        ),
        (lambda client: Models(client), "models"),
        (lambda client: GovernancePolicies(client), "policies"),
    ],
    ids=[
        "environments",
        "providers",
        "credentials",
        "models",
        "governance",
    ],
)
@pytest.mark.parametrize(
    "body_factory",
    [
        lambda key: {},
        lambda key: {key: "not-a-list"},
        lambda key: {key: ["not-an-object"]},
        lambda key: {key: [], "page": "not-an-object"},
    ],
    ids=[
        "missing-key",
        "non-list",
        "non-object-entry",
        "invalid-page",
    ],
)
def test_reject_malformed_collection_envelopes(
    client_factory,
    manager_factory,
    key,
    body_factory,
):
    """Phase 4 collection managers reject malformed response envelopes."""
    client = client_factory([body_factory(key)])

    with pytest.raises(TypeError):
        manager_factory(client).list()


def test_iteration_uses_server_page_size_when_request_is_larger():
    manager = PagedManager(
        [
            Page(list(range(25)), PageInfo(page_size=25, offset=0)),
            Page([25, 26], PageInfo(page_size=25, offset=25)),
        ]
    )

    results = list(manager.iterate(page_size=100))

    assert len(results) == 27
    assert [query["offset"] for query in manager.queries] == [0, 25]


def test_iteration_uses_server_page_size_when_size_is_omitted():
    manager = PagedManager(
        [
            Page([1, 2], PageInfo(page_size=2, offset=0)),
            Page([3], PageInfo(page_size=2, offset=2)),
        ]
    )

    assert list(manager.iterate()) == [1, 2, 3]
    assert [query["offset"] for query in manager.queries] == [0, 2]
