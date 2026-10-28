# Explain the project in plain English

Use this guide to understand the implementation, then explain it in your own words. Do not claim to understand code you have not reviewed. The README contains the exact commands; `ARCHITECTURE.md` has the detailed rules and file map.

## Fifteen teaching points

### 1. What does the application do?

It takes Elanco's educational tick sighting records, saves cleaned records locally, and lets another program request searches and summaries over HTTP. It returns JSON, a structured text format. Swagger is an interactive way to try those requests, not a separate frontend. Counts do not tell us someone's disease risk.

### 2. How does data get into the database?

Run `python -m scripts.import_sightings` using the project environment. It calls `fetch_sightings()`, which downloads the source array. It calls `normalize_record()` on each row, then `save_sightings()` for the valid rows. Finally it prints real retrieved/inserted/updated/unchanged/skipped counts. Opening a search endpoint does not download data; importing is a separate action.

### 3. What happens when data is missing?

An ID and a usable date are essential, so a row without them is skipped. Location, species and Latin name can be unknown: missing or blank text becomes `null`, meaning no value was supplied. We do not turn a missing city into London or a missing date into today. A number where a text field should be is rejected rather than guessed.

### 4. How are duplicates handled?

The source ID identifies a record. Think of it like a report reference number. The same ID and contents are unchanged; changed contents update the same row. Different reference numbers stay separate even if they share a day and city. This avoids merging two genuine reports just because they look similar. Repeating an import therefore does not keep adding copies.

### 5. How does filtering work?

FastAPI checks the query values. SQL adds only the requested conditions. `location=lon` finds a city containing that text regardless of letter case. Dates use `>= start_date` and `<= end_date`, so both ends are included. `limit` controls page size and `offset` skips earlier results. A total is returned alongside the page; no match is a normal empty response.

### 6. How are regional statistics calculated?

The SQL groups records by `location` and counts each group. The source has cities but no administrative region field. The required route is named `/stats/regions`, but its response explicitly states that it is grouped by location. We did not invent a region mapping. A missing city stays in a separate null group.

### 7. How are trends calculated?

For a month, a date such as `2024-06-18` is labelled `2024-06-01`. For a week, it is labelled with that week's Monday. SQL counts rows with the same label. Weeks work across New Year; we test that boundary. Only occupied buckets appear. Filters run first, so a bucket may contain only part of its normal week/month.

### 8. What does FastAPI do?

It connects a URL and HTTP method to a Python function. For example, `GET /health` calls the health function. Query rules reject invalid values before running a search. Response models describe the returned JSON. FastAPI also creates `/openapi.json`, which Swagger uses to show interactive documentation. Uvicorn is the process that listens for requests and runs this application.

### 9. Why SQLite?

It is a database stored in one file, available through Python's standard library. It needs no separate server, making the assessment easy to run. A transaction treats a group of writes as one unit: they succeed together or roll back together. SQLite is sufficient for this local MVP, but concurrent writers and much larger workloads would need further assessment.

### 10. Why Python?

The transformation code is short and readable, and Python includes date handling and SQLite. The choice helps keep the project explainable. It does not mean Python is automatically the fastest option for every workload; simplicity was more important here.

### 11. How are errors handled?

The downloader retries network failures, 429 rate limits and server errors only a bounded number of times. It limits response size and rejects bad JSON. A failed download leaves stored data untouched. Invalid query parameters get HTTP 422. A local database problem gets HTTP 503 with a safe message. The CLI returns a nonzero exit code so the terminal can tell it failed.

### 12. How do tests work?

pytest calls small checks and compares actual results with expected results. Synthetic fixtures are invented records labelled for testing, not real sightings. Temporary databases isolate tests from normal data. HTTPX mock transports imitate source responses, including outages, so tests work offline. Separate live verification checks the running HTTP server; browser checks confirm Swagger really rendered. Passing tests give evidence for tested cases, not proof that every possible bug is absent.

### 13. What would you improve?

First, report why individual rows were skipped and make conflicting source IDs easier to inspect. For larger data, prefer upstream pagination or incremental parsing. A reviewed city-to-region reference could support actual administrative regions. Scheduled imports need authentication and operational controls. Consider PostgreSQL only if concurrency and workload justify another service. These are future ideas, not implemented features.

### 14. What challenges were actually encountered?

The main design mismatch was that the task asks for regions but the actual source supplies cities. The solution is honest city grouping with an explicit note. The source also has no pagination, so the client uses a bounded download rather than pretending to page it. Dates have no supplied timezone, so day-level reports preserve the written date instead of inventing UTC. Dependency testing exposed a Starlette test-client deprecation warning; it is documented, not hidden. A parser-failure test was made deterministic across tested Python runtimes rather than relying on their different recursion limits.

### 15. What does each Python file do?

| File | Simple explanation |
|---|---|
| `app/__init__.py`, `scripts/__init__.py` | Mark folders as Python packages |
| `app/main.py` | Receives requests, validates filters and calls the right database function |
| `app/config.py` | Reads and checks settings; resolves the database path |
| `app/client.py` | Talks to Elanco and handles download failures |
| `app/database.py` | Creates tables, saves records, searches and counts them |
| `app/models.py` | Describes valid records and response shapes |
| `app/processing.py` | Cleans text, validates dates and renames source fields |
| `scripts/inspect_api.py` | Prints a small source-structure summary |
| `scripts/import_sightings.py` | Runs the download-clean-save process and reports counts |
| `scripts/verify_local.py` | Checks a running local API without changing its data |
| `tests/conftest.py` | Supplies shared isolated fixtures |
| `tests/test_processing.py` | Checks cleaning and invalid/missing records |
| `tests/test_import.py` | Checks mocked downloads and repeatable imports |
| `tests/test_database.py` | Checks storage, rollback and calculations |
| `tests/test_api.py` | Checks HTTP responses, filters and errors |
| `tests/test_config.py` | Checks settings and paths |
| `tests/test_verify_local.py` | Checks that the local verifier itself detects failures |

## Ten realistic interview questions

**1. Walk me through one request.**

For `GET /sightings?location=London`, FastAPI validates the query, `get_filters()` prepares it, and `get_sightings()` runs parameterised SQL. It returns a bounded page and count, checked against the response model. The request reads SQLite, not Elanco.

**2. Why not call the external API on every search?**

That would make each search depend on Elanco's speed and availability. Local storage makes searches independent after import. The trade-off is freshness: users must rerun the import to refresh the snapshot.

**3. How do you know two sightings are duplicates?**

I use the source ID, not city and date. Repeated identical IDs are unchanged, corrected contents update that ID, and different IDs remain separate. If conflicting versions of one ID occur in a response, the last valid occurrence wins.

**4. What happens if the import fails halfway through?**

If downloading fails, saving has not started. If saving fails, its transaction rolls back, including earlier writes in that transaction. Existing data is not deliberately deleted. Tests cover both cases.

**5. How did you prevent SQL injection?**

User values are passed separately through SQL placeholders. They are treated as values, not executable SQL. The weekly/monthly expression comes only from fixed code alternatives. Search text such as `%`, `_` or a quote remains literal text.

**6. Does `/stats/regions` really return UK regions?**

No. The source has cities, so it returns city-level counts and explicitly says `grouped_by: "location"`. A reviewed mapping would be needed for administrative regions; guessing would misrepresent the data.

**7. What are the limits of your large-dataset handling?**

Result pagination, indexes and one write transaction help. The source has no documented pagination, so the array is still loaded in memory, bounded by the response-size limit. Substring searches and large offsets can scan many rows. I would not claim this is an unlimited-scale solution.

**8. Why test weekly boundaries?**

Week grouping can be wrong on Sundays, Mondays or around New Year. Tests use known synthetic dates and verify Monday labels across a year boundary, rather than checking only an ordinary middle-of-month example.

**9. What does a successful health check prove?**

The local application can access its database and count stored rows. It does not prove Elanco is online, the snapshot is fresh or the educational records measure real-world risk.

**10. What would you do before exposing this publicly?**

Review authentication, access controls, deployment configuration, monitoring and update procedures. Keep imports controlled, review dependencies and reassess database concurrency. This submission deliberately binds locally and has no public hosting or admin import endpoint.

## A short explanation to practise

"I built a small FastAPI backend around the actual Elanco educational API. A separate import command validates the records and saves them in SQLite using the source ID, making repeat imports safe. Read-only endpoints provide location/date searches and city or time summaries. I tested normal behaviour and failures with synthetic fixtures and temporary databases, then checked the running API and Swagger. The main limitations are the source's lack of pagination and administrative regions, which I document rather than inventing data."
