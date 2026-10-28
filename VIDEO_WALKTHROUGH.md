# Walkthrough video plan

**Status: script only. No video has been recorded or submitted.** Target about 7 minutes; keep the final recording under 10 minutes. Replace `[YOUR FULL NAME]` before speaking. Use this as a guide, not a claim that you wrote or understand something you have not reviewed.

## Prepare before recording

1. Read the README and `INTERVIEW_GUIDE.md`; practise explaining the actual code in your own words.
2. Open this project folder in VS Code. Close unrelated tabs and notifications. Hide email, credentials, personal files and other projects.
3. Follow the README installation commands. Run the import once, then again if demonstrating repeat-import safety. Show the actual counts you receive, not a promised fixed number.
4. Start the server and leave its terminal running:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app
   ```

5. Open `http://127.0.0.1:8000/docs`. This link works only while your local server runs. In a second terminal run:

   ```powershell
   .\.venv\Scripts\python.exe -m scripts.verify_local
   .\.venv\Scripts\python.exe -m pytest -q
   ```

6. Enlarge editor/browser text until it is readable in the recording. Prepare the four routes below. Do not edit out an error in a way that falsely implies it passed; fix and rerun the demonstration.

## Speaking script and screen cues

### 0:00-0:30 - Introduction

**Show:** README overview.

"Hi, I'm [YOUR FULL NAME]. This is my backend submission for the Elanco placement task. It imports tick sighting records from the supplied API and stores a cleaned version locally. You can search by location and date, then get city counts or weekly and monthly trends. Elanco labels this an educational dataset, so these results are not live tick surveillance or a prediction of disease risk. I focused on a small, understandable backend rather than adding a separate frontend."

### 0:30-1:25 - Technologies

**Show:** `requirements.txt`, then the architecture flow.

"I used Python because the processing is readable and it already includes SQLite support. FastAPI handles the HTTP routes, validates the query parameters and generates this interactive Swagger documentation. Uvicorn runs the server. Pydantic describes the normalised records and responses.

"SQLite stores everything in one local file, so someone reviewing this project does not need to install a database server. I used the standard sqlite3 module rather than adding an ORM. HTTPX downloads the source data, and pytest checks the behaviour with mocked HTTP responses and temporary databases. The tests do not need the external API to be available. This is deliberately a local MVP, not a claim that it is ready for a large public service."

### 1:25-2:20 - Project structure

**Show:** VS Code explorer; briefly open each main file.

"The files follow the data flow. Config holds simple settings. Client handles HTTP requests and source failures. Processing cleans each source record. Models describe the fields we return. Database owns the SQL and transactions. Main creates the app and defines short routes that call those functions.

"The scripts folder contains a small API inspector, the repeatable import command and a local HTTP verifier. The tests folder checks processing, imports, database calculations and routes separately. Data contains the local database, which is ignored by Git. The README gives the commands, architecture explains the trade-offs, and the checklist tracks what still needs to be submitted. Keeping these jobs separate makes it easier to find a problem without introducing lots of layers."

### 2:20-3:25 - Data handling

**Show:** `normalize_record()`, `save_sightings()` and an actual import summary.

"I inspected the source before deciding the schema. It returns one array with id, date, location, species and latinName. There is no documented source pagination, region or coordinate field. I map the names into a consistent internal format and retain the written calendar date without guessing a timezone.

"An ID and usable date are required. Missing optional text stays null, and an invalid row is skipped and counted rather than invented. The source ID is the database key: identical repeat imports are unchanged, and corrected contents update that ID. Two different IDs in the same city on the same day remain two reports.

"The client has bounded retries, timeouts and a response-size limit. Downloading finishes before saving. All saves share a transaction, so a database failure rolls them back. If downloading fails, previous data is still there. This summary shows the actual outcome of my import."

### 3:25-5:25 - Live API demonstration

**Show:** Swagger UI. Use **Try it out**, enter values, and **Execute**. Read the actual response rather than reciting an expected count.

1. **`GET /sightings`**, `limit=3`, `offset=0`:

   "This returns a page of normalised records plus the total number matching. Results have a stable date-and-ID order, and the page size is bounded."

2. **`GET /sightings`**, `location=London`, `start_date=2024-01-01`, `end_date=2024-12-31`:

   "The filters can be combined. Location is a literal case-insensitive substring and both date boundaries are inclusive. A valid search with no matches returns an empty list, not an error. The inspected source covers 2012 to 2024, so a 2026 search is not a useful live-data demo."

3. **`GET /stats/regions`**, leave filters blank:

   "The required route is called regions, but the source only supplies cities. I make that limitation explicit with grouped_by location and a note, rather than inventing administrative regions. Each count is a number of stored reports."

4. **`GET /stats/trends`**, execute first with `period=month`, then `period=week`:

   "Monthly buckets start on day one; weekly buckets start on Monday, including across year boundaries. These reports return only buckets containing records. The same location and date filters are available, and a filtered bucket may be only part of a week or month."

### 5:25-6:25 - Error handling and tests

**Show:** `/sightings` with `start_date=2024-12-31`, `end_date=2024-01-01`; then the actual pytest output.

"Here the end date is before the start date. The API returns a useful 422 validation response instead of running a misleading search. Invalid page sizes and dates are rejected too. A local database failure gets a safe 503 message, without exposing its path.

"These are the tests I just ran. They use synthetic fixtures and isolated databases. They cover repeated imports, corrected records, missing data, upstream failures, literal search text, date boundaries, pagination, and weekly or monthly counts. There is one documented upstream test-client deprecation warning; I have not hidden it. The live verifier separately checks the running HTTP API, and I also checked that Swagger actually renders."

### 6:25-7:00 - Conclusion

**Show:** architecture limitations and checklist.

"The core backend can import, search and report on the supplied dataset, with repeatable imports and tested failure handling. The main limitations are that the source is unpaginated and only provides cities. With more time, I would add clearer skip-reason reports, a reviewed city-to-region mapping and source-supported pagination. Authentication and higher-concurrency storage would matter before public deployment. The repository contains the setup steps, tests and these decisions so the project can be reviewed and run locally. Thank you."

## Recording on Windows

- Use a screen recorder already available on your computer. On supported Windows 11 versions, Snipping Tool has a **Record** mode: select the project area, start a short test and check whether your version captures microphone audio. Features vary; do not assume audio is enabled.
- `Win+G` opens Xbox Game Bar where available. Its recording is generally app-window based and is not reliable for capturing the desktop/File Explorer or switching between multiple apps. If it cannot capture the full walkthrough, use another installed recorder rather than forcing this method.
- Record a 15-second test first. Play it back: check microphone, text size and that personal windows are not visible. Keep recording controls outside the demonstrated content where practical.
- Save the final video, play it from beginning to end, and confirm it is **no longer than 10 minutes**. Check that the code, API responses and voice are understandable.
- Use the submission's accepted file/link method. If sharing a link, test its viewing permissions in a signed-out/private window. Do not publish personal information accidentally. Add the verified link to the email draft and checklist yourself.
