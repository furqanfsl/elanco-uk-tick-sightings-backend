"""Network responses below contain only synthetic test sightings."""

import httpx
import pytest

from app.client import SourceError, fetch_sightings
from app.config import Settings
from app.database import get_sightings
from scripts.inspect_api import inspect_api
from scripts.import_sightings import import_sightings, main


@pytest.fixture
def settings(tmp_path):
    return Settings(database_path=tmp_path / "isolated.sqlite3")


@pytest.fixture
def records():
    return [
        {"id": "synthetic-1", "date": "2024-01-01T12:00:00", "location": "Example City"},
        {"id": "synthetic-2", "date": "2024-01-01T12:00:00", "location": "Example City"},
    ]


def response_transport(records):
    return httpx.MockTransport(lambda request: httpx.Response(200, json=records))


def test_repeat_import_does_not_duplicate_distinct_same_day_reports(settings, records):
    first = import_sightings(settings, transport=response_transport(records))
    second = import_sightings(settings, transport=response_transport(records))
    assert first == {"retrieved": 2, "inserted": 2, "updated": 0, "unchanged": 0, "skipped": 0, "errors": 0}
    assert second == {"retrieved": 2, "inserted": 0, "updated": 0, "unchanged": 2, "skipped": 0, "errors": 0}


def test_changed_source_id_updates_existing_record(settings, records):
    import_sightings(settings, transport=response_transport(records))
    records[0]["location"] = "Changed City"
    summary = import_sightings(settings, transport=response_transport(records))
    assert summary["updated"] == 1
    assert summary["unchanged"] == 1


def test_repeated_id_within_one_import_keeps_last_valid_version(settings):
    records = [
        {"id": "synthetic-repeat", "date": "2024-01-01", "location": "Original City"},
        {"id": "synthetic-repeat", "date": "2024-01-02", "location": "Corrected City"},
        {"id": "synthetic-repeat", "date": "bad", "location": "Invalid City"},
    ]
    summary = import_sightings(settings, transport=response_transport(records))
    assert summary == {"retrieved": 3, "inserted": 1, "updated": 1, "unchanged": 0, "skipped": 1, "errors": 0}
    page = get_sightings(settings.database_path)
    assert page["total"] == 1
    assert page["items"][0]["sighting_date"] == "2024-01-02"
    assert page["items"][0]["location"] == "Corrected City"


def test_malformed_records_are_skipped_but_missing_optional_location_is_kept(settings, records):
    records.extend([None, {"id": "bad-date", "date": "nonsense"}, {"id": "synthetic-3", "date": "2024-02-01"}])
    summary = import_sightings(settings, transport=response_transport(records))
    assert summary["retrieved"] == 5
    assert summary["inserted"] == 3
    assert summary["skipped"] == 2


def test_empty_source_is_a_valid_noop(settings):
    assert import_sightings(settings, transport=response_transport([]))["inserted"] == 0


def test_failed_refresh_preserves_previous_import(settings, records, monkeypatch):
    import_sightings(settings, transport=response_transport(records))
    monkeypatch.setattr("app.client.time.sleep", lambda seconds: None)
    with pytest.raises(SourceError):
        import_sightings(settings, transport=httpx.MockTransport(lambda request: httpx.Response(503)))
    # An unchanged repeat proves both original records are still stored.
    summary = import_sightings(settings, transport=response_transport(records))
    assert summary["unchanged"] == 2
    assert summary["inserted"] == 0


@pytest.mark.parametrize("status", [429, 500, 503])
def test_retryable_statuses_stop_after_three_attempts(settings, monkeypatch, status):
    calls = []
    monkeypatch.setattr("app.client.time.sleep", lambda seconds: None)
    def handler(request):
        calls.append(request)
        return httpx.Response(status)
    with pytest.raises(SourceError):
        fetch_sightings(settings, transport=httpx.MockTransport(handler))
    assert len(calls) == 3


def test_network_timeout_is_bounded(settings, monkeypatch):
    calls = []
    monkeypatch.setattr("app.client.time.sleep", lambda seconds: None)
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("synthetic private detail must not be exposed", request=request)
    with pytest.raises(SourceError, match="could not be reached") as error:
        fetch_sightings(settings, transport=httpx.MockTransport(handler))
    assert len(calls) == 3
    assert "private detail" not in str(error.value)


def test_transient_failure_can_recover(settings, records, monkeypatch):
    calls = []
    monkeypatch.setattr("app.client.time.sleep", lambda seconds: None)
    def handler(request):
        calls.append(request)
        return httpx.Response(503) if len(calls) == 1 else httpx.Response(200, json=records)
    assert fetch_sightings(settings, transport=httpx.MockTransport(handler)) == records
    assert len(calls) == 2


def test_configured_timeout_is_used(settings):
    def handler(request):
        assert request.extensions["timeout"]["read"] == settings.request_timeout
        assert request.extensions["timeout"]["connect"] == settings.request_timeout
        return httpx.Response(200, json=[])
    assert fetch_sightings(settings, transport=httpx.MockTransport(handler)) == []


def test_non_retryable_status_is_not_retried(settings):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(404, text="private body")
    with pytest.raises(SourceError, match="HTTP 404") as error:
        fetch_sightings(settings, transport=httpx.MockTransport(handler))
    assert len(calls) == 1
    assert "private body" not in str(error.value)


@pytest.mark.parametrize("payload", [b"not json", b"\xff", b'{"records": []}', b"null"])
def test_invalid_json_or_wrong_top_level_is_reported(settings, payload):
    with pytest.raises(SourceError):
        fetch_sightings(settings, transport=httpx.MockTransport(lambda request: httpx.Response(200, content=payload)))


def test_oversized_response_is_rejected(settings):
    settings = Settings(database_path=settings.database_path, max_response_bytes=5)
    with pytest.raises(SourceError, match="size limit"):
        fetch_sightings(settings, transport=response_transport([{"large": "x" * 20}]))


def test_size_limit_stops_reading_stream_and_closes_it(settings):
    class OversizedStream(httpx.SyncByteStream):
        def __init__(self):
            self.chunks_read = 0
            self.closed = False

        def __iter__(self):
            for chunk in [b"[", b'"' + b"x" * 32, b'"]']:
                self.chunks_read += 1
                yield chunk

        def close(self):
            self.closed = True

    stream = OversizedStream()
    settings = Settings(database_path=settings.database_path, max_response_bytes=10)
    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=stream))
    with pytest.raises(SourceError, match="size limit"):
        fetch_sightings(settings, transport=transport)
    assert stream.chunks_read == 2
    assert stream.closed is True
    assert not settings.database_path.exists()


def test_json_parser_recursion_has_safe_cli_error(settings, capsys, monkeypatch):
    # Parser nesting limits differ across Python versions; simulate the failure itself.
    def nesting_limit(body):
        raise RecursionError("synthetic parser nesting limit")

    monkeypatch.setattr("app.client.json.loads", nesting_limit)
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b"[]"))
    assert main(settings, transport=transport) == 1
    assert "Traceback" not in capsys.readouterr().err
    assert not settings.database_path.exists()


def test_long_rate_limit_does_not_retry_too_early(settings):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(429, headers={"Retry-After": "60"})
    with pytest.raises(SourceError, match="rate limit"):
        fetch_sightings(settings, transport=httpx.MockTransport(handler))
    assert len(calls) == 1


def test_cli_failure_has_clear_nonzero_result_and_no_traceback(settings, capsys):
    result = main(settings, transport=httpx.MockTransport(lambda request: httpx.Response(404)))
    output = capsys.readouterr()
    assert result == 1
    assert "Import failed:" in output.err
    assert "Traceback" not in output.err
    assert not settings.database_path.exists()


def test_cli_database_error_is_nonzero_and_does_not_expose_path(settings, records, capsys):
    # A directory cannot be opened as a SQLite file on Windows or Unix.
    settings.database_path.mkdir()
    assert main(settings, transport=response_transport(records)) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "local database could not be written" in output.err
    assert str(settings.database_path) not in output.err
    assert "Traceback" not in output.err


def test_cli_prints_actual_counts(settings, records, capsys):
    assert main(settings, transport=response_transport(records)) == 0
    assert '"inserted": 2' in capsys.readouterr().out


def test_inspection_reports_structure_without_returning_raw_sightings(settings, records):
    summary = inspect_api(settings, transport=response_transport(records))
    assert summary["records"] == 2
    assert summary["field_types"]["id"] == ["str"]
    assert summary["missing_or_blank"]["species"] == 2
    assert "synthetic-1" not in str(summary)
