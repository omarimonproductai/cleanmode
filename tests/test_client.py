import responses

from mode_cleanup.client import ModeClient
from mode_cleanup.config import Config

CONFIG = Config(workspace="cooltra", api_token="tok", api_secret="sec")
WS = "https://app.mode.com/api/cooltra"


@responses.activate
def test_get_smoke_data_sources():
    responses.add(
        responses.GET,
        f"{WS}/data_sources",
        json={"_embedded": {"data_sources": [{"id": 1, "name": "Snowflake"}]}},
        status=200,
    )
    client = ModeClient(CONFIG)
    payload = client.get("data_sources")
    assert payload["_embedded"]["data_sources"][0]["name"] == "Snowflake"


@responses.activate
def test_paginate_follows_next_link():
    responses.add(
        responses.GET,
        f"{WS}/spaces",
        json={
            "_embedded": {"spaces": [{"token": "a"}]},
            "_links": {"next": {"href": "/api/cooltra/spaces?page=2"}},
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{WS}/spaces?page=2",
        json={"_embedded": {"spaces": [{"token": "b"}]}, "_links": {}},
        status=200,
    )
    client = ModeClient(CONFIG)
    tokens = [s["token"] for s in client.paginate("spaces", "spaces")]
    assert tokens == ["a", "b"]


@responses.activate
def test_get_retries_on_429_then_succeeds():
    responses.add(responses.GET, f"{WS}/data_sources", status=429)
    responses.add(
        responses.GET,
        f"{WS}/data_sources",
        json={"_embedded": {"data_sources": []}},
        status=200,
    )
    # backoff_base=0 perquè el test no esperi.
    client = ModeClient(CONFIG, backoff_base=0)
    payload = client.get("data_sources")
    assert payload["_embedded"]["data_sources"] == []
    assert len(responses.calls) == 2
