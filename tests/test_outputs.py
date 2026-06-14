import csv

from mode_cleanup.outputs import (
    INVENTORY_CSV,
    REPORT_HTML,
    REPORTS_CSV,
    SUMMARY_MD,
    write_outputs,
)
from mode_cleanup.process import InventoryRow, ReportRow


def _rows():
    inventory = [
        InventoryRow(
            data_source_name="(morta/desconeguda)",
            data_source_id=999,
            data_source_alive="no",
            report_name="Old",
            report_token="r2",
            report_url="",
            space_name="Personal",
            query_name="q_old",
            last_run_at="",
            days_since_last_run="mai",
            owner="",
            is_archived="si",
        ),
        InventoryRow(
            data_source_name="Snowflake",
            data_source_id=10,
            data_source_alive="si",
            report_name="Live",
            report_token="r1",
            report_url="https://app.mode.com/x/r1",
            space_name="Analytics",
            query_name="q_live",
            last_run_at="2026-06-04T00:00:00Z",
            days_since_last_run=10,
            owner="oriol",
            is_archived="no",
        ),
    ]
    reports = [
        ReportRow(
            report_name="Old",
            report_token="r2",
            report_url="https://app.mode.com/editor/ecooltra706/reports/r2",
            space_name="Personal",
            owner="",
            last_run_at="",
            days_since_last_run="mai",
            is_archived="si",
            query_count=1,
            data_source_count=1,
            purity="pure",
            pure_source="(morta/desconeguda)",
            data_sources="(morta/desconeguda)",
            has_dead_source="si",
        ),
    ]
    return inventory, reports


def test_write_outputs_creates_files(tmp_path):
    inventory, reports = _rows()
    paths = write_outputs(inventory, reports, tmp_path)

    assert (tmp_path / INVENTORY_CSV).exists()
    assert (tmp_path / REPORTS_CSV).exists()
    assert (tmp_path / SUMMARY_MD).exists()

    with (tmp_path / INVENTORY_CSV).open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["data_source_alive"] == "no"
    assert rows[0]["data_source_name"] == "(morta/desconeguda)"

    summary = (tmp_path / SUMMARY_MD).read_text(encoding="utf-8")
    assert "Queries cap a fonts mortes/desconegudes: **1**" in summary
    assert "Reports mai executats: **1**" in summary

    # HTML autònom amb les dades incrustades.
    html = (tmp_path / REPORT_HTML).read_text(encoding="utf-8")
    assert "Inventari de reports MODE" in html
    assert "https://app.mode.com/editor/ecooltra706/reports/r2" in html
    assert "__DATA__" not in html  # el placeholder s'ha substituït
