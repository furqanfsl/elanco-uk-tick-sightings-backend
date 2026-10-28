# Elanco UK Tick Sightings Backend

Public repository: [furqanfsl/elanco-uk-tick-sightings-backend](https://github.com/furqanfsl/elanco-uk-tick-sightings-backend)

## Overview

A small, read-only Python backend that imports the Elanco placement-task tick dataset, cleans it, stores it in SQLite, and returns searchable records and summaries as JSON. Swagger UI provides an interactive way to try the endpoints; there is no separate frontend.

## Purpose

Location and time summaries demonstrate how a tick-reporting service could help people explore reported activity. **Elanco explicitly labels this source as an educational dataset. These counts are not live surveillance, infection rates, or a measure of disease risk.**

## Features

- Imports the documented API with timeouts, bounded retries and a response-size limit.
- Validates dates and IDs, cleans text, retains missing optional fields as `null`, and skips invalid records.
- Uses the source ID to prevent duplicate imports and update corrected records.
- Searches city names and inclusive date ranges, with bounded result pagination.
- Reports city-level counts and Monday-based weekly or calendar-month trends.
- Preserves stored data when the external service fails; returns useful validation and database errors.

## Technologies used

Python keeps the processing readable. FastAPI handles HTTP routes, validation and API documentation. Python's built-in `sqlite3` stores records without another database server. HTTPX calls the source API. Pydantic describes response data; pytest checks behaviour. Uvicorn runs the application. Starlette, FastAPI's HTTP layer, is explicitly pinned to the tested version.

## Project structure

```text
app/
  __init__.py             Python package marker
  main.py                 Routes, validation, lifespan and safe database errors
  config.py               Environment settings and project-relative database path
  client.py               HTTP requests, retries, size limit and source errors
  database.py             SQLite schema, transactional saves, filters and reports
  models.py               Normalised sighting and response contracts
  processing.py           Source-field mapping, text cleaning and date validation
scripts/
  __init__.py             Python package marker
  inspect_api.py          Small schema/missing-field summary, not a data dump
  import_sightings.py     Repeatable command-line import and actual counts
  verify_local.py         Read-only checks against a running local server
tests/
  conftest.py             Disposable database and synthetic API fixtures
  test_api.py             Routes, filtering, reports and invalid inputs
  test_processing.py      Cleaning and missing/invalid source fields
  test_import.py          Mocked HTTP failures, imports and repeat-import safety
  test_database.py        Storage, rollback, filtering and calendar boundaries
  test_config.py          Configuration validation
  test_verify_local.py    Local verification success/failure paths
data/.gitkeep             Keeps the empty data directory in Git
.env.example             Safe configuration reference (not automatically loaded)
.gitignore               Excludes environments, local data, credentials and caches
requirements.txt         Tested dependency versions
ARCHITECTURE.md           Data flow, decisions and limitations
VIDEO_WALKTHROUGH.md      Recording preparation and a 6–8 minute speaking script
SUBMISSION_CHECKLIST.md   Requirement evidence, remaining deliverables and email draft
INTERVIEW_GUIDE.md        Plain-English explanation and ten interview questions
```

The extra database/configuration/verifier tests isolate useful regressions. No downloaded source data or database is included in the repository.

## Installation — Windows PowerShell

Prerequisites: Python 3.12 or later, Internet access for installation/import, and Git if cloning the repository. Python downloads: [python.org](https://www.python.org/downloads/). The verified runtimes were Python 3.12.13 and 3.15.2 on Windows. Use an ordinary PowerShell terminal in the project folder.

```powershell
git clone https://github.com/furqanfsl/elanco-uk-tick-sightings-backend.git
cd elanco-uk-tick-sightings-backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

These commands use the environment's interpreter directly, so activation and execution-policy changes are unnecessary. If you prefer activation, run `.\.venv\Scripts\Activate.ps1`, then use `python` for the commands below. If activation is blocked, use the direct commands instead; do not weaken system-wide security settings.

In VS Code, open this project folder, run **Python: Select Interpreter**, and choose `.venv\Scripts\python.exe` if the Python extension is already available. No additional extension is needed to run the terminal commands.

## Running the application

```powershell
# Optional: inspect the source structure without printing the dataset.
.\.venv\Scripts\python.exe -m scripts.inspect_api

# Download, clean and store data. Repeat this command to refresh it.
.\.venv\Scripts\python.exe -m scripts.import_sightings

# Start the server and leave this terminal running.
.\.venv\Scripts\python.exe -m uvicorn app.main:app
```

Open [Swagger UI](http://127.0.0.1:8000/docs) or the [health check](http://127.0.0.1:8000/health) in your browser. **Localhost links require the server to be running on your computer. Clicking a link does not launch it, and this is not a public deployment.** Press `Ctrl+C` to stop the server. Restart it after editing Python files; a reload watcher is not required.

In a second terminal, from the same folder:

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_local
```

This checks the running HTTP API without contacting Elanco or modifying data. Browser rendering is a separate check. Without an import, the application returns valid empty results and the verifier explicitly skips checks that need records.

### Configuration

Defaults work without configuration. `.env.example` documents supported environment variables, but the application does **not** load `.env` files automatically. For example:

```powershell
$env:ELANCO_DATABASE_PATH = 'data/another-local.db'
$env:ELANCO_REQUEST_TIMEOUT = '10'
```

Relative database paths resolve from the project folder, not the terminal's current directory. The source defaults to `https://dev-task.elancoapps.com/data/tick-sightings`; the decoded response limit defaults to 5 MiB. Set the same database setting for both import and server terminals. Restart after changing settings.

### Troubleshooting

- **Connection refused:** start Uvicorn and wait for “Application startup complete”, then reload the local link. A stopped server cannot serve a landing page.
- **Port 8000 already in use:** identify its owner. Stop only your own previous server with `Ctrl+C`, or deliberately configure another port and use that address consistently. Do not kill unrelated processes. The supplied verifier intentionally checks port 8000 by default.
- **Python launcher missing:** install Python from the official link, then reopen the terminal. If `py -3` cannot find a runtime, inspect `py list` (new launcher) or `py -0p` (legacy launcher), and use the installed Python executable with `-m venv .venv`. On the development computer the existing 3.12 runtime was selected with `py -V:Astral/CPython3.12.13`; the clean `py -3` setup was separately verified with 3.15.2.
- **No results:** run the import and inspect its counts. The inspected source dates were 2012–2024, so a 2026 filter correctly returns no records.
- **Import fails:** read the short error, wait if rate-limited, and retry later. Stored data remains available. Invalid source rows are counted as skipped, not silently turned into invented records.
- **Database error/HTTP 503:** check the local path, folder permissions and whether another program is holding a write lock. Do not delete the database to fix a failed refresh.
- **Swagger loads blank:** check Internet access to its standard Swagger CDN assets. The JSON endpoints and `/openapi.json` do not depend on that CDN. There is no custom frontend; `/docs` adds small contrast, language and focus fixes to the standard Swagger UI. Operation-path deep links are disabled to avoid nested interactive controls.

## API endpoints

| Method | Endpoint | Purpose / parameters |
|---|---|---|
| GET | `/` | Introduction and documentation link |
| GET | `/health` | Local database check and stored row count; no upstream request |
| GET | `/sightings` | `location`, `start_date`, `end_date`, `limit` (1–200), `offset` (0–9223372036854775807) |
| GET | `/stats/regions` | City-level counts; same location/date filters |
| GET | `/stats/trends` | `period=week` or `period=month`; same location/date filters |

Examples after starting the server:

- [Sightings page](http://127.0.0.1:8000/sightings?limit=5)
- [London city filter](http://127.0.0.1:8000/sightings?location=London)
- [2024 date filter](http://127.0.0.1:8000/sightings?start_date=2024-01-01&end_date=2024-12-31)
- [City counts](http://127.0.0.1:8000/stats/regions)
- [Weekly counts](http://127.0.0.1:8000/stats/trends?period=week)

Location matching is a literal, case-insensitive substring, so `%` and `_` are ordinary characters, not wildcards. Results sort by date descending, then source ID ascending. Dates must be real `YYYY-MM-DD` calendar dates; both boundaries are inclusive. Invalid input returns HTTP 422. Database failures return a safe HTTP 503 response without database paths or secrets.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use small, explicitly synthetic fixtures and temporary databases; HTTP requests to Elanco are mocked. They do not depend on the live source or modify the normal database. A single upstream Starlette warning currently notes that its legacy HTTPX test-client adapter is deprecated. It is still supported and tests pass; dependencies were not downgraded or the warning hidden merely to silence it.

## Design decisions

The source was inspected before implementation. Its public documentation is at [Elanco's API site](https://dev-task.elancoapps.com/), with an embedded OpenAPI specification. The actual dataset endpoint returns a single array with `id`, `date`, `location`, `species`, and `latinName`. No authentication or pagination is documented. The site documents HTTP 429 rate limiting but does not specify a request quota. The guessed `/docs`, `/openapi.json` and `/redoc` paths on that external site returned 404; those are not the source API paths.

`id` becomes `source_id`, `date` becomes a day-level `sighting_date`, and `latinName` becomes `latin_name`. Missing ID or unusable date means the row is skipped. Optional missing/blank location and species fields remain `null`; non-text values and oversized text are rejected. Source clock time is deliberately discarded; its written calendar date is retained without inventing a timezone. A stable source ID is the primary key: changed contents update that ID, identical repeats are unchanged, and different IDs on the same day/city remain distinct. If one response repeats an ID with conflicting contents, the last valid occurrence wins; summary counts describe processing operations, not distinct input IDs.

All saves in one import share a transaction. Failed downloads do not touch the database; failed saves roll back. Imports do not delete records missing from a later response. Fetching is a separate CLI command rather than an unauthenticated administrative route.

SQLite is sufficient for this portable, single-machine MVP. Parameterised queries protect user-supplied values. Date and location/date indexes are created; substring city searches can still require a scan. Count and result page use one database snapshot. Further explanation is in [ARCHITECTURE.md](ARCHITECTURE.md).

## Challenges and limitations

- **No region field:** `/stats/regions` honestly reports the supplied cities and returns `grouped_by: "location"`. These are geographic location groups, **not inferred administrative regions**. A missing location is a separate `null` group, not a fictional city.
- **Unpaginated source:** the client must parse one array in memory. It streams the response into a bounded buffer (5 MiB default), rejects larger payloads, and uses one database transaction. True source pagination/streaming would need an upstream change or a different parser.
- **Network failures:** at most three attempts on network errors, 429 and 5xx; short backoff; HTTPX's 10-second operation/inactivity timeouts are not a single wall-clock deadline. Long/date-form `Retry-After` windows stop the import and ask the user to retry later.
- **Reports:** weeks start Monday; months start on day 1. Only occupied buckets are returned. A date-filtered bucket may contain a partial week/month; its label is the bucket's first day, possibly before `start_date`. Counts do not estimate population exposure or disease prevalence.
- **Local MVP:** no authentication, scheduling, public hosting, medical predictions or AI/ML. It binds to localhost by default. Do not expose it publicly without further security review.
- The normalised table is not an archive of the full original source. The source data and local database are intentionally excluded from Git.

## Future improvements

With more time: source-supported pagination, conflict/skip-reason reports, a reviewed city-to-region reference dataset, scheduled authenticated imports, better monitoring, and PostgreSQL for higher concurrency. A frontend could consume these endpoints later; none is needed for this backend assessment.

## Author

**Hafiz Furqan FAISEL**

## Assignment information

Prepared for the Elanco Software Engineering Placement 2026 backend technical assessment. The walkthrough and final email are prepared as drafts, not recorded or sent. Complete [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) before submitting.

## Launch verification — 28 October 2026

Working local startup and accurate instructions are part of this submission. Latest observed checks are recorded here; this is not a hosted deployment:

- Python 3.12.13 local environment: **117 tests passed, 0 failed**, with the one upstream deprecation warning described above.
- Clean `py -3` virtual-environment installation with Python 3.15.2: installation, the full **117 tests**, and `pip check` passed. The same documented warning applies.
- Real source import: **1,000 inserted**, then **1,000 unchanged** on repeat; zero skipped/errors. No source records are bundled in Git.
- Uvicorn started on `127.0.0.1:8000`; health returned 1,000 rows. London matched 76; the 2024 date filter matched 71. City, week and month report totals each reconciled to 1,000 (14 cities, 522 occupied weeks, 156 months).
- Local verifier: **24 checks passed, 0 skipped** after restarting the documented server command. Stopped server correctly produced a concise failure and browser connection refusal, then the same localhost URL worked after restart. No port was changed or unrelated process stopped.
- Swagger rendered in headless Microsoft Edge at 1440px desktop and 390px mobile. Default, expanded, success and HTTP 422 states passed the scoped automated accessibility checks (8 states, zero reported violations), with no JavaScript errors or horizontal overflow. Before/after and success/error-detail screenshots were saved in the temporary `elanco-backend-20261028-qa` directory and inspected for layout, typography, colour, surfaces, writing and accessibility; contrast, button overlap and mobile code scrolling were corrected. This is not a full accessibility certification. Native browser-control connection was unavailable; actual headless browser testing was used, not an HTTP-only claim.
- `pip check`, Python compilation and a dependency audit of the installed project environment passed. The initial virtual environment's old pip bootstrap had known advisories; pip was upgraded to 26.2.2 and the repeated audit reported **no known vulnerabilities**. The audit tool itself was installed only in a temporary environment, not added to application requirements.
