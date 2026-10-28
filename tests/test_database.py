"""Database tests use synthetic sightings and temporary SQLite files only."""

import sqlite3

import pytest

from app.database import (
    count_all,
    count_sightings_by_region,
    get_sightings,
    get_trends,
    init_database,
    save_sightings,
)
from app.models import Sighting


def sighting(source_id="synthetic-1", sighting_date="2024-01-01", **changes):
    values = {
        "source_id": source_id,
        "sighting_date": sighting_date,
        "location": "Example City",
        "species": "Synthetic species",
        "latin_name": "Syntheticus testus",
    }
    values.update(changes)
    return Sighting(**values)


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "test.sqlite3"
    init_database(path)
    return path


def test_empty_database(database_path):
    assert count_all(database_path) == 0
    assert get_sightings(database_path) == {"items": [], "total": 0, "limit": 50, "offset": 0}
    assert count_sightings_by_region(database_path) == []
    assert get_trends(database_path) == []


def test_repeated_import_and_correction(database_path):
    record = sighting()
    assert save_sightings(database_path, [record]) == {"inserted": 1, "updated": 0, "unchanged": 0}
    assert save_sightings(database_path, [record]) == {"inserted": 0, "updated": 0, "unchanged": 1}
    assert save_sightings(database_path, [sighting(location="Corrected City")]) == {
        "inserted": 0, "updated": 1, "unchanged": 0
    }
    assert count_all(database_path) == 1
    assert get_sightings(database_path)["items"][0]["location"] == "Corrected City"


def test_distinct_ids_same_date_and_place_are_kept(database_path):
    save_sightings(database_path, [sighting("synthetic-a"), sighting("synthetic-b")])
    assert count_all(database_path) == 2


def test_filters_dates_pagination_and_stable_order(database_path):
    save_sightings(database_path, [
        sighting("synthetic-b", "2024-01-02", location="Example City"),
        sighting("synthetic-a", "2024-01-02", location="Example City"),
        sighting("synthetic-c", "2024-01-03", location="Other City"),
        sighting("synthetic-d", "2023-12-31", location="Example City"),
    ])
    result = get_sightings(
        database_path, location="eXaMpLe", start_date="2024-01-01",
        end_date="2024-01-02", limit=1, offset=1,
    )
    assert result["total"] == 2
    assert result["items"][0]["source_id"] == "synthetic-b"
    assert result["limit"] == 1
    assert result["offset"] == 1
    assert get_sightings(database_path, offset=99)["items"] == []


@pytest.mark.parametrize("query", ["%", "_", "' OR 1=1 --"])
def test_search_is_literal_and_parameterised(database_path, query):
    save_sightings(database_path, [sighting()])
    assert get_sightings(database_path, location=query)["total"] == 0
    assert count_all(database_path) == 1


def test_missing_location_is_reported_without_inventing_one(database_path):
    save_sightings(database_path, [sighting("synthetic-a", location=None), sighting("synthetic-b")])
    assert count_sightings_by_region(database_path) == [
        {"region": None, "count": 1}, {"region": "Example City", "count": 1}
    ]


def test_region_counts_use_locations_and_shared_filters(database_path):
    save_sightings(database_path, [
        sighting("synthetic-a", "2024-01-01", location="Alpha"),
        sighting("synthetic-b", "2024-01-02", location="Beta"),
        sighting("synthetic-c", "2024-01-03", location="Alpha"),
    ])
    assert count_sightings_by_region(database_path) == [
        {"region": "Alpha", "count": 2}, {"region": "Beta", "count": 1}
    ]
    assert count_sightings_by_region(database_path, start_date="2024-01-02", location="beta") == [
        {"region": "Beta", "count": 1}
    ]


def test_monthly_trends_are_first_of_month_without_filled_gaps(database_path):
    save_sightings(database_path, [
        sighting("synthetic-a", "2023-12-31"),
        sighting("synthetic-b", "2024-01-01"),
        sighting("synthetic-c", "2024-01-31"),
        sighting("synthetic-d", "2024-03-01"),
    ])
    assert get_trends(database_path, period="month") == [
        {"period_start": "2023-12-01", "count": 1},
        {"period_start": "2024-01-01", "count": 2},
        {"period_start": "2024-03-01", "count": 1},
    ]


def test_weekly_trends_monday_sunday_and_year_boundary(database_path):
    save_sightings(database_path, [
        sighting("synthetic-a", "2023-12-31"),  # Sunday, previous calendar week.
        sighting("synthetic-b", "2024-01-01"),  # Monday starts a new week.
        sighting("synthetic-c", "2024-01-07"),
        sighting("synthetic-d", "2024-01-08"),
    ])
    assert get_trends(database_path, period="week") == [
        {"period_start": "2023-12-25", "count": 1},
        {"period_start": "2024-01-01", "count": 2},
        {"period_start": "2024-01-08", "count": 1},
    ]


def test_trend_filters_run_before_grouping(database_path):
    save_sightings(database_path, [
        sighting("synthetic-a", "2024-01-01", location="Alpha"),
        sighting("synthetic-b", "2024-01-02", location="Beta"),
        sighting("synthetic-c", "2024-01-03", location="Alpha"),
    ])
    assert get_trends(database_path, location="alpha", start_date="2024-01-02") == [
        {"period_start": "2024-01-01", "count": 1}
    ]


def test_invalid_period_is_not_interpolated_into_sql(database_path):
    with pytest.raises(ValueError, match="week or month"):
        get_trends(database_path, period="month'; DROP TABLE sightings; --")
    assert count_all(database_path) == 0


def test_save_rolls_back_partial_changes(database_path):
    save_sightings(database_path, [sighting()])

    def broken_records():
        yield sighting("synthetic-new")
        raise RuntimeError("Synthetic import failure")

    with pytest.raises(RuntimeError, match="Synthetic import failure"):
        save_sightings(database_path, broken_records())
    assert count_all(database_path) == 1


def test_read_errors_are_not_hidden(tmp_path):
    with pytest.raises(sqlite3.Error):
        count_all(tmp_path / "missing-parent" / "test.sqlite3")


def test_initialisation_is_repeatable_and_creates_parent(tmp_path):
    path = tmp_path / "new-folder" / "test.sqlite3"
    init_database(path)
    init_database(path)
    assert count_all(path) == 0
