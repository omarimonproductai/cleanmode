import responses

from mode_cleanup.client import ModeClient
from mode_cleanup.collect import collect_all
from mode_cleanup.config import Config

CONFIG = Config(workspace="ecooltra706", api_token="tok", api_secret="sec")
WS = "https://app.mode.com/api/ecooltra706"


@responses.activate
def test_collect_all_gathers_reports_with_queries():
    responses.add(
        responses.GET,
        f"{WS}/data_sources",
        json={"_embedded": {"data_sources": [{"id": 10, "name": "Snowflake"}]}},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{WS}/spaces",
        json={"_embedded": {"spaces": [{"token": "sp1", "name": "Analytics"}]}},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{WS}/collections/sp1/reports",
        json={
            "_embedded": {
                "reports": [
                    {"token": "r1", "name": "Daily", "archived": False},
                    {"token": "r2", "name": "Old", "archived": True},
                ]
            }
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{WS}/reports/r1/queries",
        json={"_embedded": {"queries": [{"name": "q1", "data_source_id": 10}]}},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{WS}/reports/r2/queries",
        json={"_embedded": {"queries": []}},
        status=200,
    )

    result = collect_all(ModeClient(CONFIG))

    assert len(result.data_sources) == 1
    # Inclou també el report arxivat (r2).
    assert {r.report["token"] for r in result.reports} == {"r1", "r2"}
    r1 = next(r for r in result.reports if r.report["token"] == "r1")
    assert r1.space_name == "Analytics"
    assert r1.queries[0]["data_source_id"] == 10


@responses.activate
def test_collect_follows_hal_reports_link_and_skips_404_space():
    responses.add(
        responses.GET,
        f"{WS}/data_sources",
        json={"_embedded": {"data_sources": []}},
        status=200,
    )
    # Un espai dóna un enllaç HAL de reports propi; un altre dóna 404.
    responses.add(
        responses.GET,
        f"{WS}/spaces",
        json={
            "_embedded": {
                "spaces": [
                    {
                        "token": "sp_ok",
                        "name": "OK",
                        "_links": {
                            "reports": {"href": "/api/ecooltra706/spaces/sp_ok/reports"}
                        },
                    },
                    {"token": "sp_bad", "name": "Privat"},
                ]
            }
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{WS}/spaces/sp_ok/reports",
        json={"_embedded": {"reports": [{"token": "r1", "name": "OK report"}]}},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{WS}/collections/sp_bad/reports",
        json={"id": "not_found", "message": "space not found"},
        status=404,
    )
    responses.add(
        responses.GET,
        f"{WS}/reports/r1/queries",
        json={"_embedded": {"queries": []}},
        status=200,
    )

    result = collect_all(ModeClient(CONFIG))
    # L'espai 404 s'ha saltat; només queda el report de l'espai accessible.
    assert {r.report["token"] for r in result.reports} == {"r1"}


@responses.activate
def test_collect_with_explicit_collection_tokens():
    responses.add(
        responses.GET,
        f"{WS}/data_sources",
        json={"_embedded": {"data_sources": []}},
        status=200,
    )
    # Nom de la col·lecció via detail.
    responses.add(
        responses.GET,
        f"{WS}/collections/tok123",
        json={"name": "Finance"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{WS}/collections/tok123/reports",
        json={"_embedded": {"reports": [{"token": "rA", "name": "A"}]}},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{WS}/reports/rA/queries",
        json={"_embedded": {"queries": [{"name": "q", "data_source_id": 5}]}},
        status=200,
    )

    result = collect_all(ModeClient(CONFIG), collection_tokens=["tok123"])
    assert len(result.reports) == 1
    assert result.reports[0].space_name == "Finance"
    assert result.reports[0].report["token"] == "rA"
