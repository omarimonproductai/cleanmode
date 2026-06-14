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


def test_purity_mixed_and_pure():
    _, reports = process(_collected(), now=NOW, workspace="ecooltra706")
    r1 = [r for r in reports if r.report_token == "r1"][0]
    # r1 té una query live (Snowflake) i una morta -> mixed, amb font morta.
    assert r1.purity == "mixed"
    assert r1.data_source_count == 2
    assert r1.has_dead_source == "si"
    assert r1.query_count == 2

    r2 = [r for r in reports if r.report_token == "r2"][0]
    # r2 té només una query morta -> pure (d'una sola font, la morta).
    assert r2.purity == "pure"
    assert r2.pure_source == DEAD_SOURCE_LABEL


def test_report_url_editor_format():
    _, reports = process(_collected(), now=NOW, workspace="ecooltra706")
    r1 = [r for r in reports if r.report_token == "r1"][0]
    assert r1.report_url == "https://app.mode.com/editor/ecooltra706/reports/r1"
    r2 = [r for r in reports if r.report_token == "r2"][0]
    assert r2.report_url == "https://app.mode.com/editor/ecooltra706/reports/r2"
