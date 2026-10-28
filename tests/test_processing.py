"""Small synthetic records, not copied Elanco sightings."""

import pytest

from app.processing import normalize_record


@pytest.fixture
def record():
    return {
        "id": "synthetic-1",
        "date": "2024-02-29T14:30:00",
        "location": "  Example   City  ",
        "species": " Example tick ",
        "latinName": " Example species ",
    }


def test_normalizes_source_names_and_calendar_date(record):
    sighting = normalize_record(record)
    assert sighting.source_id == "synthetic-1"
    assert sighting.sighting_date == "2024-02-29"
    assert sighting.location == "Example City"
    assert sighting.species == "Example tick"
    assert sighting.latin_name == "Example species"


@pytest.mark.parametrize("missing", ["location", "species", "latinName"])
def test_missing_optional_values_remain_null(record, missing):
    del record[missing]
    sighting = normalize_record(record)
    field = "latin_name" if missing == "latinName" else missing
    assert getattr(sighting, field) is None


@pytest.mark.parametrize("value", [None, "", "  \t "])
def test_blank_optional_values_become_null(record, value):
    record["location"] = value
    assert normalize_record(record).location is None


@pytest.mark.parametrize("value", ["2024-01-01", "2024-01-01T23:45:00Z", "2024-01-01T23:45:00-05:00"])
def test_preserves_written_calendar_day_without_guessing_timezone(record, value):
    record["date"] = value
    assert normalize_record(record).sighting_date == "2024-01-01"


@pytest.mark.parametrize("field,value", [
    ("id", None), ("id", ""), ("id", 42), ("id", "x" * 201),
    ("date", None), ("date", 42), ("date", "2023-02-29T12:00:00"),
    ("date", "01/02/2024"), ("date", "2024-01-01junk"),
    ("date", "2024-01-01T25:00:00"), ("location", ["Example City"]),
    ("species", {"name": "Example tick"}), ("latinName", "x" * 201),
])
def test_rejects_invalid_required_or_non_text_values(record, field, value):
    record[field] = value
    with pytest.raises(ValueError):
        normalize_record(record)


@pytest.mark.parametrize("value", [None, [], "bad", 1])
def test_non_object_records_are_invalid(value):
    with pytest.raises(ValueError):
        normalize_record(value)


def test_does_not_use_date_and_location_as_an_identity(record):
    another = dict(record, id="synthetic-2")
    assert normalize_record(record).source_id != normalize_record(another).source_id
