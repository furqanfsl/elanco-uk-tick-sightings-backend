"""Check a running local backend. This command never imports source data."""

import sys
from datetime import date

import httpx

DEFAULT_URL = "http://127.0.0.1:8000"


class VerificationError(Exception):
    """A failed local check, without a raw response or traceback."""


def verify_local(base_url: str = DEFAULT_URL, *, transport=None) -> dict:
    url = httpx.URL(base_url)
    if url.scheme != "http" or url.host not in {"127.0.0.1", "localhost", "::1"}:
        raise VerificationError("Use a loopback HTTP address for local verification.")
    passed = skipped = 0

    def check(condition, name):
        nonlocal passed
        if not condition:
            raise VerificationError(name)
        passed += 1
        print(f"PASS {name}")

    def count_rows(rows):
        if not isinstance(rows, list) or not all(
            isinstance(row, dict) and type(row.get("count")) is int and row["count"] > 0 for row in rows
        ):
            raise VerificationError("Report rows must contain positive integer counts.")
        return sum(row["count"] for row in rows)

    with httpx.Client(base_url=base_url, timeout=10, transport=transport) as client:
        def get(path, params=None, *, html=False):
            response = client.get(path, params=params)
            if response.status_code != 200:
                raise VerificationError(f"GET {path} returned HTTP {response.status_code}, expected 200.")
            if html:
                return response.text
            try:
                body = response.json()
            except ValueError:
                raise VerificationError(f"GET {path} did not return valid JSON.") from None
            if not isinstance(body, dict):
                raise VerificationError(f"GET {path} did not return a JSON object.")
            return body

        check(get("/").get("documentation") == "/docs", "Home links to documentation")
        check("SwaggerUIBundle" in get("/docs", html=True), "Swagger HTML is served (browser rendering checked separately)")
        paths = get("/openapi.json").get("paths", {})
        check(all("get" in paths.get(path, {}) for path in ["/", "/health", "/sightings", "/stats/regions", "/stats/trends"]), "OpenAPI lists every required route")
        health = get("/health")
        stored = health.get("stored_sightings")
        check(health.get("status") == "ok" and health.get("database") == "ok" and type(stored) is int and stored >= 0, "Backend and database are healthy")
        page = get("/sightings", {"limit": 2, "offset": 0})
        items = page.get("items", [])
        check(page.get("total") == stored and len(items) == min(2, stored) and page.get("limit") == 2, "Paginated count matches health")
        next_page = get("/sightings", {"limit": 1, "offset": 1})
        check(next_page.get("items") == items[1:2] and next_page.get("total") == stored, "Pagination offset returns the next record")
        tail = get("/sightings", {"limit": 1, "offset": stored})
        check(tail.get("items") == [] and tail.get("total") == stored, "Offset beyond the dataset is empty")
        no_match = get("/sightings", {"location": "___local_verification_no_city_5c420a___"})
        check(no_match.get("items") == [] and no_match.get("total") == 0, "Unmatched location returns an empty result")
        regions = get("/stats/regions")
        check(regions.get("grouped_by") == "location" and count_rows(regions.get("regions")) == stored, "City summary totals match stored sightings")
        for period in ["week", "month"]:
            trends = get("/stats/trends", {"period": period})
            rows = trends.get("trends")
            check(trends.get("period") == period and count_rows(rows) == stored, f"{period.title()} trend totals match stored sightings")
            starts = [date.fromisoformat(row["period_start"]) for row in rows]
            check(all(day.weekday() == 0 if period == "week" else day.day == 1 for day in starts), f"{period.title()} buckets use calendar boundaries")
        if items:
            row = next((item for item in items if item.get("location")), items[0])
            day = row["sighting_date"]
            filtered = get("/sightings", {"start_date": day, "end_date": day, "limit": 200})
            check(filtered["total"] >= 1 and all(item["sighting_date"] == day for item in filtered["items"]), "Inclusive single-day date filter")
            if row.get("location"):
                location = row["location"]
                filtered = get("/sightings", {"location": location, "limit": 200})
                check(filtered["total"] >= 1 and all(location.lower() in (item["location"] or "").lower() for item in filtered["items"]), "Location filter matches discovered city")
                params = {"location": location, "start_date": day, "end_date": day}
                filtered = get("/sightings", params)
                check(filtered["total"] >= 1 and all(item["sighting_date"] == day and location.lower() in item["location"].lower() for item in filtered["items"]), "Combined location and date filters")
                check(count_rows(get("/stats/regions", params)["regions"]) == filtered["total"], "Filtered report matches filtered sightings")
            else:
                skipped += 1
                print("SKIP location filters: sampled records have no supplied location")
        else:
            skipped += 1
            print("SKIP populated-data filter checks: database is empty; run the import first")
        for name, path, params in [
            ("Date syntax", "/sightings", {"start_date": "not-a-date"}),
            ("Invalid calendar day", "/sightings", {"start_date": "2024-02-30"}),
            ("Reversed date range", "/sightings", {"start_date": "2024-02-02", "end_date": "2024-02-01"}),
            ("Negative limit", "/sightings", {"limit": -1}), ("Oversized page", "/sightings", {"limit": 201}),
            ("Negative offset", "/sightings", {"offset": -1}), ("Unsupported period", "/stats/trends", {"period": "year"}),
        ]:
            check(client.get(path, params=params).status_code == 422, f"{name} rejected with HTTP 422")
    print(f"Local verification: {passed} passed, {skipped} skipped; {stored} stored sightings.")
    return {"passed": passed, "skipped": skipped, "stored": stored}


def main(base_url: str = DEFAULT_URL, *, transport=None) -> int:
    try:
        verify_local(base_url, transport=transport)
    except httpx.RequestError:
        print("FAIL Cannot reach the local backend. Start the server, then retry. The localhost URL requires a running server; the link does not launch it.", file=sys.stderr)
        return 1
    except (VerificationError, ValueError, KeyError, TypeError) as error:
        message = str(error) if isinstance(error, VerificationError) else "The backend returned an unexpected response structure."
        print(f"FAIL {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
