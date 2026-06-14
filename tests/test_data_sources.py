import csv

from mode_cleanup.outputs import DATA_SOURCES_CSV, write_data_sources
from mode_cleanup.process import process_data_sources

RAW = [
    {
        "name": "Snowflake",
        "token": "tok1",
        "id": "100",
        "adapter": "jdbc:snowflake",
        "vendor": "snowflake",
        "provider": None,
        "host": "h1",
        "database": "db",
        "queryable": True,
        "asleep": False,
        "soft_deleted": False,
        "public": False,
        "default_access_level": "View",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "_links": {"creator": {"href": "/api/robertoleta"}},
    },
    {
        "name": "App_FirebaseEvents",
        "token": "tok2",
        "id": "200",
        "adapter": "jdbc:bigquery",
        "vendor": "bigquery",
        "asleep": True,
        "soft_deleted": False,
        "queryable": True,
        "_links": {},
    },
]


def test_process_data_sources_maps_and_sorts():
    rows = process_data_sources(RAW)
    # Ordenat per nom: App_FirebaseEvents abans que Snowflake.
    assert [r.name for r in rows] == ["App_FirebaseEvents", "Snowflake"]
    fb = rows[0]
    assert fb.asleep == "si"
    assert fb.creator == ""
    snow = rows[1]
    assert snow.creator == "robertoleta"
    assert snow.asleep == "no"
    assert snow.provider == ""  # None normalitzat a buit


def test_write_data_sources_csv(tmp_path):
    rows = process_data_sources(RAW)
    path = write_data_sources(rows, tmp_path)
    assert path == tmp_path / DATA_SOURCES_CSV
    with path.open(encoding="utf-8") as fh:
        out = list(csv.DictReader(fh))
    assert out[0]["name"] == "App_FirebaseEvents"
    assert out[1]["creator"] == "robertoleta"
