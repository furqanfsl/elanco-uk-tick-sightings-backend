# Explain the project in plain English

Use this guide to understand the implementation, then explain it in your own words. Do not claim to understand code you have not reviewed. The README contains the exact commands; `ARCHITECTURE.md` has the detailed rules and file map.

## Part A: Explain the project

This is the Backend assessment option selected for this submission. It focuses on the data pipeline, storage, searches and reports rather than a separate frontend. Give your own reason for choosing Backend if asked; do not invent a personal motivation.

The problem it addresses is that a raw list of reports is difficult to search or summarise by eye. Its main features are repeatable imports, validated records, local storage, city/date searches and location/time summaries. The following explanations follow its actual data flow.

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

## Part B: Explain the important files

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

### Main functions, inputs and outputs

| File | Main code | Input | Output and connections |
|---|---|---|---|
| `app/main.py` | `create_app()`, `get_filters()`; route functions `home()`, `health()`, `sightings()`, `regions()`, `trends()` | Settings and HTTP queries | JSON, 422 or safe 503; calls database functions and response models. `app = create_app()` is Uvicorn's entry object. |
| `app/config.py` | `Settings`, `get_settings()` | Environment variables | Checked source URL, path, timeout and size limit; shared by API/scripts. Relative paths resolve from the project folder; `.env` is not loaded automatically. |
| `app/client.py` | `fetch_sightings()`, `SourceError` | Settings; optional mock transport in tests | Source list or a concise error; called by import/inspection scripts. No cleaning or SQL here. |
| `app/processing.py` | `clean_text()`, `parse_sighting_date()`, `normalize_record()` | One raw source record | A `Sighting` or `ValueError`; used before storage. Maps `id`/`date`/`latinName` to internal names. |
| `app/models.py` | `Sighting`, `SightingsPage`, `RegionCount`, `RegionalReport`, `TrendCount`, `TrendReport`, `HealthResponse`; `valid_calendar_date()` | Normalised data and query results | Validated field/response shapes used by processing and FastAPI. Swagger examples are synthetic. |
| `app/database.py` | `init_database()`, `save_sightings()`, `count_all()`, `get_sightings()`, `count_sightings_by_region()`, `get_trends()` | Database path, sighting models or query options | Save counters, page/count or report rows; owns SQL and closes connections. Called by scripts/routes. |
| `scripts/import_sightings.py` | `import_sightings()`, `main()` | Settings and downloaded records | Actual import counters; CLI exit 0/1. Connects fetch, normalisation and transactional save. |
| `scripts/inspect_api.py` | `inspect_api()`, `main()` | Configured source response | Compact count/field/type/missing-value summary; shares client/settings and does not save sightings. |
| `scripts/verify_local.py` | `verify_local()`, `main()`, `VerificationError` | Loopback URL; optional test transport | Pass/skip summary or exit 1; reads local endpoints without importing source data. Browser rendering is checked separately. |

The package `__init__.py` files contain no business logic. `tests/conftest.py` supplies temporary `api` and `populated_api` fixtures. The test files take synthetic records, requests or mocked responses and output assertions; they must not change the normal database or depend on Elanco being online.

Other important files are `requirements.txt` (dependencies), `.env.example` (safe settings reference), `.gitignore` (private/generated exclusions), and `.vscode/tasks.json` (shortcuts for the same terminal commands, not another server implementation).

## Part C: Technical concepts

| Concept | Meaning and example in this application |
|---|---|
| Python | The language used for downloading, cleaning, SQL calls and routes. |
| FastAPI | Connects HTTP URLs to functions, validates query values and generates the API schema. |
| REST API | An HTTP interface organised around resources. `GET /sightings` reads sighting resources; this small read-only API does not implement every possible REST operation. |
| HTTP GET | A request to read data; it does not create or delete sightings here. |
| Query parameters | Options after `?`, such as `/sightings?location=London&limit=3`. |
| JSON | Structured text with objects, lists and values, such as `items` and `total`. |
| SQLite | A database stored in one file, accessed through Python's built-in `sqlite3`. |
| Database table | Rows with named columns; `sightings` stores one row per source ID. |
| SQL | The language for database operations; `SELECT COUNT(*) FROM sightings` counts rows. |
| Primary key | A value identifying one row; here it is `source_id`. |
| Parameterised query | SQL and values are supplied separately through placeholders such as `?`. |
| SQL injection | An attempt to make input execute as SQL; placeholders keep a quoted search from becoming a command. |
| Data validation | Checking usability, such as rejecting `2024-02-30` or a negative page size. |
| Data cleaning | Making valid values consistent, such as collapsing spaces or renaming source fields. |
| Deduplication | Avoiding repeated copies of one source ID; different IDs stay distinct. |
| Aggregation | Summarising rows, such as `GROUP BY location` for city counts. |
| Error handling | Turning expected failures into useful outcomes: a CLI error, HTTP 422 or safe HTTP 503. |
| Unit testing | A focused check of one behaviour, such as normalising a date. |
| Integration testing | Checking pieces together, such as a route reading a temporary database. It need not use the live service. |

Two other useful terms: **pagination** returns a limited page instead of every row; a **transaction** makes a batch of writes succeed together or roll back together.

## Part D: Twenty interview questions

### 1. Why did you choose Python?

It keeps the transformation code readable and includes date handling and SQLite. Simplicity and explainability mattered more than adding a complex stack; Python is not automatically the fastest option for every workload.

### 2. Why did you choose FastAPI?

It provides clear routes, query validation, response models and OpenAPI/Swagger documentation. That keeps the assessment focused on the backend and data rather than building a separate interface.

### 3. Why did you choose SQLite?

It needs no separate server and makes the MVP portable. One file is enough for this small local dataset. Concurrent writers and much larger workloads would need further assessment.

### 4. How is the external API used?

The separate import command calls `GET https://dev-task.elancoapps.com/data/tick-sightings` through HTTPX. The inspected endpoint returns one array without documented authentication or pagination. Searches read the saved snapshot, not Elanco.

### 5. How are sightings stored?

The table stores source ID, day-level date, location, species and Latin name. The default file is `data/sightings.db`, excluded from Git. ISO day strings keep sorting and filtering consistent.

### 6. How are duplicates prevented?

The source ID is the primary key. An identical repeat is unchanged; corrected contents update that row. Different IDs on the same day/city stay separate. Within one response, the last valid conflicting occurrence wins; import counters describe processing operations.

### 7. How are incomplete records handled?

An ID and usable date are essential; unusable rows are skipped and counted. Missing optional location, species or Latin name stays null. Wrong types are rejected rather than guessed. Missing dates or geographical fields are never invented.

### 8. How does location filtering work?

It is a literal case-insensitive city substring. `location=lon` can match London, while `%` and `_` are ordinary characters, not wildcards. SQL values use placeholders. SQLite's simple lowercasing is adequate for the inspected ASCII city names, not a general Unicode search solution.

### 9. How does date filtering work?

Inputs must be real `YYYY-MM-DD` dates. The conditions are `>= start_date` and `<= end_date`, so both ends are included and either boundary can be used alone. A reversed range returns HTTP 422.

### 10. How are regional statistics calculated?

The source supplies cities, not administrative regions. SQL groups by `location` and counts each group. The response explicitly says `grouped_by: "location"`; null location is its own group. A reviewed reference would be needed for administrative regions.

### 11. How do you calculate weekly trends?

Each date is labelled with its week's Monday, then rows sharing that label are counted. This works across New Year instead of confusing a week number with a calendar year. Tests cover Sunday, Monday and year boundaries.

### 12. How do you calculate monthly trends?

Dates are labelled with day one of their month, then counted. Both trend types sort chronologically and return only occupied buckets. Filters run first, so a bucket may represent only part of its week or month.

### 13. What happens when Elanco's API fails?

Network failures, HTTP 429 and 5xx get at most three attempts with short backoff. Long rate-limit windows stop the import rather than retrying too early. Bad JSON, other non-200 statuses and oversized responses produce useful errors. Fetching happens before saving, so old records remain. The timeout is for network operations/inactivity, not one total deadline.

### 14. How do you validate user inputs?

FastAPI checks types and bounds: page size 1-200, bounded nonnegative offset, and week/month period. `get_filters()` checks real dates, date order and nonblank location text. Invalid requests return HTTP 422 before a misleading query runs.

### 15. How did you test the application?

pytest uses synthetic fixtures, temporary databases and HTTPX mocks. Tests cover processing, imports, rollback, filters, calendar boundaries and errors. The local verifier checks the running HTTP server; browser checks confirm Swagger renders. Use the latest README for observed counts. Passing tested cases is not proof that every possible bug is absent.

### 16. What challenges did you encounter?

The source has cities but no regions and no documented pagination, so those limitations are explicit. Dates lack a supplied timezone, so reports retain their written day. Review found oversized-offset and deeply nested JSON failures; bounds/error handling and regressions addressed them. A parser-exception test was made deterministic across Python versions. The upstream test-client warning is documented, not hidden.

### 17. What would you improve with more time?

Clearer skip/conflict-reason reports, a reviewed city-to-region reference and source-supported pagination would help. Authentication, scheduling and monitoring matter before public deployment. These are future improvements, not implemented features.

### 18. How would you scale the application?

Measure the workload first. Pagination, indexes and one write transaction help now, but substring searches, large offsets and full counts can be expensive. Consider upstream pagination, cursor pagination and a server database when concurrency warrants them. The bounded source array is still parsed in memory.

### 19. How would you make the application more secure?

Keep SQL parameterised, imports controlled and private files out of Git. Before exposing the server, review authentication, TLS deployment, access controls, monitoring, dependency updates and request limits. This MVP binds locally and has no data-modifying HTTP endpoint. A public code repository is not a deployed public API.

### 20. What did you learn from this project?

Answer personally after reviewing it. A factual starting point is: "This project shows why I should inspect a source before designing its schema, use stable IDs for repeatable imports, separate external failures from local searches, and test calendar boundaries." Do not claim learning or experience you have not gained.

## Part E: Five-minute revision guide

**Minute 1:** Import -> HTTPX -> validation -> SQLite. Request -> FastAPI validation -> SQL -> JSON. Importing and searching are separate.

**Minute 2:** Source ID prevents repeat copies. Different IDs remain distinct. Required ID/date failure means skip; optional missing text means null. Nothing is invented.

**Minute 3:** Literal case-insensitive city substring; inclusive dates; bounded page and stable order. Cities are not administrative regions. Weeks start Monday; months start on day one; empty buckets are omitted.

**Minute 4:** Bounded source attempts and byte cap; fetch before writing; failed saves roll back. HTTP 422 means invalid input; safe HTTP 503 means database unavailable. Synthetic tests are separate from live verification.

**Minute 5:** The data is educational, not live risk surveillance. SQLite is simple, not unlimited-scale storage. The source is unpaginated and saved data can be stale. Production security and scheduling are future work.

Practise these points without reading, then open a relevant function and explain its input and output. Study anything unclear before the interview.

### Port reminder

Port 5500 is a static-file server if Live Server is running; its directory listing does not execute Python. Use the README's Uvicorn command and `http://127.0.0.1:8000/docs` for the backend. A localhost link requires a running process and is not a public deployment.

## A short explanation to practise

"I built a small FastAPI backend around the actual Elanco educational API. A separate import command validates the records and saves them in SQLite using the source ID, making repeat imports safe. Read-only endpoints provide location/date searches and city or time summaries. I tested normal behaviour and failures with synthetic fixtures and temporary databases, then checked the running API and Swagger. The main limitations are the source's lack of pagination and administrative regions, which I document rather than inventing data."
