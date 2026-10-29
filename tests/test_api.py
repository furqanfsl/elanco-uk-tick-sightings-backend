"""Endpoint tests use synthetic records in a disposable database."""
import sqlite3

import pytest


def test_home_and_documentation(api):
    assert api.get("/").json()["documentation"] == "/docs"
    assert api.get("/docs").status_code == 200
    assert "#0063a6" in api.get("/docs").text
    assert '<html lang="en">' in api.get("/docs").text
    assert '"deepLinking": false' in api.get("/docs").text
    assert set(api.get("/openapi.json").json()["paths"]) == {
        "/", "/health", "/sightings", "/stats/regions", "/stats/trends"
    }


def test_health(populated_api):
    assert populated_api.get("/health").json() == {
        "status": "ok", "database": "ok", "stored_sightings": 4
    }


def test_empty_responses(api):
    assert api.get("/sightings").json() == {"items": [], "total": 0, "limit": 50, "offset": 0}
    assert api.get("/stats/regions").json()["regions"] == []
    assert api.get("/stats/trends").json()["trends"] == []


def test_sightings_pagination(populated_api):
    data = populated_api.get("/sightings?limit=2&offset=1").json()
    assert data["total"] == 4
    assert [r["source_id"] for r in data["items"]] == ["synthetic-c", "synthetic-b"]
    assert populated_api.get("/sightings?offset=99").json()["items"] == []


def test_maximum_pagination_boundaries_are_accepted(populated_api):
    page = populated_api.get("/sightings", params={"limit": 200, "offset": 0})
    assert page.status_code == 200
    assert len(page.json()["items"]) == page.json()["total"] == 4
    assert page.json()["limit"] == 200

    last_offset = 9223372036854775807
    beyond_end = populated_api.get("/sightings", params={"offset": last_offset})
    assert beyond_end.status_code == 200
    assert beyond_end.json() == {"items": [], "total": 4, "limit": 50, "offset": last_offset}


def test_literal_case_insensitive_location(populated_api):
    assert populated_api.get("/sightings?location=EXAMPLE").json()["total"] == 2
    for location in ["%", "_", "' OR 1=1 --", "absent"]:
        assert populated_api.get("/sightings", params={"location": location}).json()["total"] == 0


def test_inclusive_date_filter(populated_api):
    response = populated_api.get("/sightings?start_date=2025-12-29&end_date=2026-01-01")
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_regions_are_honest_city_counts(populated_api):
    report = populated_api.get("/stats/regions").json()
    assert report["grouped_by"] == "location"
    assert {r["region"]: r["count"] for r in report["regions"]} == {
        "Example City": 2, "Other City": 1, None: 1
    }


def test_weekly_trends_across_year(populated_api):
    result = populated_api.get("/stats/trends?period=week").json()["trends"]
    assert result == [{"period_start": "2025-12-22", "count": 1},
                      {"period_start": "2025-12-29", "count": 3}]


def test_monthly_trends(populated_api):
    assert populated_api.get("/stats/trends?period=month").json()["trends"] == [
        {"period_start": "2025-12-01", "count": 2},
        {"period_start": "2026-01-01", "count": 2},
    ]


@pytest.mark.parametrize("path", ["/sightings", "/stats/regions", "/stats/trends"])
def test_reports_share_filters(populated_api, path):
    response = populated_api.get(path, params={"location": "example", "start_date": "2025-12-29"})
    assert response.status_code == 200
    data = response.json()
    if path == "/sightings":
        assert data["total"] == 1
    else:
        key = "regions" if path.endswith("regions") else "trends"
        assert sum(row["count"] for row in data[key]) == 1


@pytest.mark.parametrize("query", [
    "start_date=bad", "start_date=2026-02-30", "start_date=20260101",
    "start_date=2026-01-02&end_date=2026-01-01", "location=%20%20",
    "limit=0", "limit=-1", "limit=201", "offset=-1", "limit=abc",
    "offset=9223372036854775808", "offset=" + "9" * 100,
])
def test_invalid_queries(api, query):
    response = api.get("/sightings?" + query)
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.parametrize("path", ["/stats/regions", "/stats/trends"])
def test_invalid_range_on_reports(api, path):
    assert api.get(path + "?start_date=2026-02-01&end_date=2026-01-01").status_code == 422


def test_invalid_period(api):
    assert api.get("/stats/trends?period=year").status_code == 422


@pytest.mark.parametrize("path", ["/health", "/sightings", "/stats/regions", "/stats/trends"])
def test_database_failure_is_safe(api, monkeypatch, path):
    from app import database

    def unavailable(*args, **kwargs):
        raise sqlite3.OperationalError("private/path/password must not be exposed")

    for name in ["count_all", "get_sightings", "count_sightings_by_region", "get_trends"]:
        monkeypatch.setattr(database, name, unavailable)
    response = api.get(path)
    assert response.status_code == 503
    assert response.json() == {"detail": "Local database unavailable. Check its path and permissions, then try again."}
