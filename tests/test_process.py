from datetime import datetime, timezone

from mode_cleanup.collect import Collected, CollectedReport
from mode_cleanup.process import DEAD_SOURCE_LABEL, NEVER_RUN, process

NOW = datetime(2026, 6, 14, tzinfo=timezone.utc)


def _collected():
    data_sources = [{"id": 10, "name": "Snowflake"}]
    reports = [
        CollectedReport(
            report={
                "token": "r1",
                "name": "Live report",
                "archived": False,
                "last_successfully_run_at": "2026-06-04T00:00:00Z",
                "account_username": "oriol",
                "_links": {"web": {"href": "https://app.mode.com/x/r1"}},
            },
            space_name="Analytics",
            queries=[
                {"name": "q_live", "data_source_id": 10},
                {"name": "q_dead", "data_source_id": 999},
            ],
        ),
        CollectedReport(
            report={"token": "r2", "name": "Never run", "archived": True},
            space_name="Personal",
            queries=[{"name": "q_old", "data_source_id": 999}],
        ),
    ]
    return Collected(data_sources=data_sources, reports=reports)


def test_dead_source_is_flagged():
    inventory, _ = process(_collected(), now=NOW)
    dead = [r for r in inventory if r.query_name == "q_dead"][0]
    assert dead.data_source_alive == "no"
    assert dead.data_source_name == DEAD_SOURCE_LABEL

    live = [r for r in inventory if r.query_name == "q_live"][0]
    assert live.data_source_alive == "si"
    assert live.data_source_name == "Snowflake"


def test_days_since_last_run_and_never():
    inventory, reports = process(_collected(), now=NOW)
    live = [r for r in inventory if r.query_name == "q_live"][0]
    assert live.days_since_last_run == 10

    never = [r for r in reports if r.report_token == "r2"][0]
    assert never.days_since_last_run == NEVER_RUN


def test_report_rows_sorted_never_run_first():
    _, reports = process(_collected(), now=NOW)
    # El que no s'ha executat mai ha d'anar primer (més antic).
    assert reports[0].report_token == "r2"


def test_archived_flag_preserved():
    _, reports = process(_collected(), now=NOW)
    r2 = [r for r in reports if r.report_token == "r2"][0]
    assert r2.is_archived == "si"
