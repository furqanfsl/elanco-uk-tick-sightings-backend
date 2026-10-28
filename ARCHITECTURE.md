# Architecture

## Data flow

```text
Elanco educational API
        |
        v
HTTPX download (scripts.import_sightings -> app.client)
        |
        v
Validation and cleaning (app.processing + app.models)
        |
        v
SQLite transaction (app.database)
        |
        v
Read-only FastAPI routes (app.main)
        |
        v
JSON responses / standard Swagger UI
```

Importing and serving are separate commands. Opening `/sightings` reads the local database; it does not call Elanco. That keeps requests predictable and preserves access to previously imported records during an upstream outage. It also means the database is a snapshot, not a live feed. Refresh it by rerunning the import command in the README.

## Source contract and normalisation

The inspected endpoint is `GET https://dev-task.elancoapps.com/data/tick-sightings`. It returns one JSON array, without documented authentication or pagination. Elanco describes the data as educational. At inspection on 28 October 2026 there were 1,000 records, dated 3 January 2012 to 30 December 2024. These observations are not guarantees about future responses.

| Source field | Stored field | Rule |
|---|---|---|
| `id` | `source_id` | Required nonblank text, at most 200 characters; trim surrounding whitespace |
| `date` | `sighting_date` | Required valid ISO date/timestamp; keep its written calendar day as `YYYY-MM-DD` |
| `location` | `location` | Optional city text; missing/blank becomes `null` |
| `species` | `species` | Optional text; missing/blank becomes `null` |
| `latinName` | `latin_name` | Optional text; missing/blank becomes `null` |

Optional text has whitespace collapsed and a 200-character limit. Non-text values are invalid rather than silently converted. Invalid records are skipped and counted. Missing dates and locations are never invented. The source has no region, coordinates or timezone field; none is inferred. Source clock time is intentionally discarded because the requested reports operate at day, week and month level.

## Why these tools?

- **Python:** readable processing code and built-in date/SQLite support.
- **FastAPI and Pydantic:** query validation, response models and generated OpenAPI documentation. Route functions validate and delegate instead of containing SQL.
- **SQLite through `sqlite3`:** one portable local file, with no separate server or ORM. Appropriate for this small, single-machine MVP, not a claim of unlimited scale.
- **HTTPX:** explicit HTTP timeouts, status handling and mock transports for tests.
- **pytest:** small independent checks using temporary databases and synthetic records.
- **Uvicorn:** the local application server.

## Storage and repeat imports

`sightings` contains one row per `source_id`, which is the primary key. There is no separate generated identity because the source already supplies one.

`save_sightings()` compares each normalised record with the stored row:

1. New ID: insert it.
2. Same ID and same contents: count it as unchanged.
3. Same ID and changed contents: update that row.

Different IDs on the same day in the same city remain separate reports. An ID repeated with conflicting contents within one response is processed in order: the last valid occurrence wins. Import counters describe processing operations, not necessarily distinct input IDs. Records absent from a later response are not deleted; this is a repeatable import, not an authoritative mirror or deletion synchroniser.

All row saves share one `BEGIN IMMEDIATE` transaction. A failed save rolls the transaction back. Downloading and normalising happen before that write transaction, so network delays do not hold the write lock. No data is cleared on a failed refresh.

## Filtering and reports

All user values use SQL placeholders, not string interpolation. The SQL expression for a trend is selected from two fixed alternatives, never from arbitrary input.

- `/sightings`: literal case-insensitive location substring, inclusive date boundaries, `limit` 1-200 and nonnegative bounded `offset`. A count and page share one read snapshot. Ordering is date descending, then source ID ascending.
- `/stats/regions`: `GROUP BY location`, with a count for each supplied city. The response explicitly says `grouped_by: "location"`. These are **not administrative regions**. A missing location is its own `null` group.
- `/stats/trends?period=week`: move each sighting date back to its Monday, then count records sharing that date.
- `/stats/trends?period=month`: use the first day of the sighting's month, then count records sharing that date.

Reports apply the same location/date filters before grouping. Only occupied buckets appear; missing weeks/months are not filled with zeroes. A filtered result can contain a partial bucket whose start label precedes `start_date`. Counts are reports in an educational dataset, not population-adjusted risk or disease prevalence.

Date and location/date indexes are created. A substring search using `instr(lower(...))` can still scan rows; the location index is not a promise that every search is indexed. Pagination bounds response size, but large offsets and full counts can become expensive.

## Error handling and limits

The HTTP client makes at most three attempts for network errors, HTTP 429 and 5xx responses, with short backoff. Other non-200 statuses fail without repeated requests. A long or date-form `Retry-After` stops the import and asks the user to retry later, rather than retrying early. HTTPX's default configured 10-second timeout applies to network operations/inactivity, not a single total wall-clock deadline.

Decoded response bytes are bounded to 5 MiB by default. Invalid JSON, a non-array response and oversized responses produce concise source errors. The source is unpaginated: the bounded array and normalised records are still held in memory. True pagination or incremental parsing would require further work.

Invalid query values return HTTP 422. SQLite failures return HTTP 503 with a safe explanation; database paths and raw exceptions are not returned. Startup initialises the schema. `/health` checks only the local database and row count, not upstream availability. The CLI exits nonzero on failure.

## File responsibilities

| File | Responsibility |
|---|---|
| `app/__init__.py`, `scripts/__init__.py` | Python package markers |
| `app/main.py` | Application factory, startup, query validation, routes, safe database errors and standard Swagger page with small accessibility overrides |
| `app/config.py` | Validated environment settings and project-relative database path; does not load `.env` automatically |
| `app/client.py` | Bounded download, retries, JSON parsing and source errors |
| `app/database.py` | Schema, connections, transactional saves, parameterised filters and summaries |
| `app/models.py` | Pydantic sighting and JSON response contracts |
| `app/processing.py` | Field mapping, text cleaning and date validation |
| `scripts/inspect_api.py` | Compact schema, types and missing-field summary, not a source-data dump |
| `scripts/import_sightings.py` | Fetch, normalise, save and report actual import counts |
| `scripts/verify_local.py` | Read-only checks against a running local HTTP server |
| `tests/conftest.py` | Isolated API/database and explicitly synthetic fixtures |
| `tests/test_api.py` | Routes, input validation, filters, reporting and safe errors |
| `tests/test_processing.py` | Cleaning, missing values, dates and source identity |
| `tests/test_import.py` | Mocked HTTP, retries, failure preservation and import counts |
| `tests/test_database.py` | Transactions, stable ordering, literal search and report boundaries |
| `tests/test_config.py` | Path and configuration validation |
| `tests/test_verify_local.py` | Verification success, skips and failures |

`requirements.txt` pins the tested direct dependencies. `.env.example` is a safe reference. `.gitignore` excludes local data, environments, private settings, caches and session notes. `data/.gitkeep` preserves an empty directory without publishing the database. The README contains setup and observed launch results; the walkthrough, checklist and interview guide support the human submission.

## Scope and next improvements

No frontend, AI/ML, scheduled refresh, authentication or public hosting is included. Bind to localhost; public exposure needs further security work. With more time: a reviewed city-to-region reference, skip/conflict-reason reporting, source-supported pagination, authenticated scheduled imports, monitoring, and a database such as PostgreSQL if concurrent use justified it. Avoid adding those components merely to make this assessment look larger.
