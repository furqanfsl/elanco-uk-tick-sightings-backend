"""Verify the local-check command without a real network or source API."""

import httpx
import pytest

from scripts.verify_local import main, verify_local


def api_transport(api):
    def handler(request):
        response = api.get(str(request.url.copy_with(scheme="http", host="testserver")))
        return httpx.Response(response.status_code, content=response.content, headers=response.headers)
    return httpx.MockTransport(handler)


def test_local_verifier_checks_populated_backend_without_dumping_records(populated_api, capsys):
    summary = verify_local(transport=api_transport(populated_api))
    output = capsys.readouterr().out
    assert summary["stored"] == 4
    assert summary["passed"] >= 15
    assert summary["skipped"] == 0
    assert "PASS" in output
    assert "synthetic-a" not in output
    assert "Example City" not in output


def test_local_verifier_handles_empty_database_honestly(api, capsys):
    summary = verify_local(transport=api_transport(api))
    assert summary["stored"] == 0
    assert summary["skipped"] == 1
    assert "SKIP populated-data filter checks" in capsys.readouterr().out


def test_cli_connection_failure_explains_startup_without_traceback(capsys):
    def handler(request):
        raise httpx.ConnectError("private synthetic network detail", request=request)
    assert main(transport=httpx.MockTransport(handler)) == 1
    output = capsys.readouterr()
    assert "Start the server" in output.err
    assert "does not launch" in output.err
    assert "Traceback" not in output.err
    assert "private synthetic" not in output.err


@pytest.mark.parametrize("path", ["/health", "/stats/regions", "/stats/trends"])
def test_cli_fails_when_reported_totals_are_inconsistent(populated_api, path, capsys):
    delegate = api_transport(populated_api)
    def handler(request):
        response = delegate.handle_request(request)
        if request.url.path == path:
            body = response.json()
            if path == "/health":
                body["stored_sightings"] = 99
            elif path == "/stats/regions":
                body["regions"][0]["count"] += 1
            else:
                body["trends"][0]["count"] += 1
            return httpx.Response(200, json=body)
        return response
    assert main(transport=httpx.MockTransport(handler)) == 1
    assert "FAIL" in capsys.readouterr().err


def test_cli_reports_invalid_json_concisely(capsys):
    assert main(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"not JSON"))) == 1
    assert "FAIL" in capsys.readouterr().err


def test_verifier_refuses_nonlocal_source_address_before_any_request(capsys):
    def handler(request):
        pytest.fail("The verifier must never request the Elanco source")
    assert main("https://dev-task.elancoapps.com", transport=httpx.MockTransport(handler)) == 1
    assert "loopback" in capsys.readouterr().err


def test_verifier_fails_if_backend_accepts_invalid_input(populated_api, capsys):
    delegate = api_transport(populated_api)
    def handler(request):
        if request.url.params.get("start_date") == "not-a-date":
            return httpx.Response(200, json={"items": [], "total": 0})
        return delegate.handle_request(request)
    assert main(transport=httpx.MockTransport(handler)) == 1
    assert "Date syntax rejected" in capsys.readouterr().err
