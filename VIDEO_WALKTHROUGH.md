# Walkthrough video plan

**Status: script only. No video has been recorded or submitted.** Target 7-8 minutes; keep the final recording under 10 minutes. The candidate name matches the GitHub profile; confirm the preferred spoken name before recording. Use this as a guide, not a claim that you wrote or understand something you have not reviewed.

## Prepare before recording

1. Read the README and `INTERVIEW_GUIDE.md`; practise explaining the actual code in your own words.
2. Open this project folder in VS Code. Close unrelated tabs and notifications. Hide email, credentials, personal files and other projects.
3. Follow the README installation commands. Run the import once, then again if demonstrating repeat-import safety. Show the actual counts you receive, not a promised fixed number.
4. Start the server and leave its terminal running:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

5. Open `http://127.0.0.1:8000/docs`. This link works only while your local server runs. In a second terminal run:

   ```powershell
   .\.venv\Scripts\python.exe -m scripts.verify_local
   .\.venv\Scripts\python.exe -m pytest -q
   ```

6. Enlarge editor/browser text until it is readable in the recording. Practise the requests below and collapse routes you are not using. Do not edit out an error in a way that falsely implies it passed; fix and rerun the demonstration. No source editing is needed during recording.
7. Use port **8000**, not Live Server/Go Live on port 5500. A static directory listing cannot run FastAPI. If the backend is already running, reuse it; do not start a second copy on the same port. The VS Code default build task (`Ctrl+Shift+B`) runs the same backend command.

## Speaking script and screen cues

### 0:00-0:40 - Introduction

**Show:** README overview.

"Hi, I'm Hafiz Furqan FAISEL. This is my backend submission for the Elanco placement task. It imports tick sighting records from the supplied API and stores a cleaned version locally. You can search by location and date, then get city counts or weekly and monthly trends. Elanco labels this an educational dataset, so these results are not live tick surveillance or a prediction of disease risk. I focused on a small, understandable backend rather than adding a separate frontend."

### 0:40-1:30 - Technologies

**Show:** `requirements.txt`, then the architecture flow.

"I used Python because the processing is readable and it already includes SQLite support. FastAPI handles the HTTP routes, validates the query parameters and generates this interactive Swagger documentation. Uvicorn runs the server. Pydantic describes the normalised records and responses.

"SQLite stores everything in one local file, so someone reviewing this project does not need to install a database server. I used the standard sqlite3 module rather than adding an ORM. HTTPX downloads the source data, and pytest checks the behaviour with mocked HTTP responses and temporary databases. The tests do not need the external API to be available. This is deliberately a local MVP, not a claim that it is ready for a large public service."

### 1:30-2:30 - Project structure

**Show:** VS Code explorer; briefly open each main file.

"The files follow the data flow. Config holds simple settings. Client handles HTTP requests and source failures. Processing cleans each source record. Models describe the fields we return. Database owns the SQL and transactions. Main creates the app and defines short routes that call those functions.

"The scripts folder contains a small API inspector, the repeatable import command and a local HTTP verifier. The tests folder checks processing, imports, database calculations and routes separately. Data contains the local database, which is ignored by Git. The README gives the commands, architecture explains the trade-offs, and the checklist tracks what still needs to be submitted. Keeping these jobs separate makes it easier to find a problem without introducing lots of layers."

### 2:30-3:30 - Data handling

**Show:** `normalize_record()`, `save_sightings()` and an actual import summary.

"I inspected the source before deciding the schema. It returns one array with id, date, location, species and latinName. There is no documented source pagination, region or coordinate field. I map the names into a consistent internal format and retain the written calendar date without guessing a timezone.

"An ID and usable date are required. Missing optional text stays null, and an invalid row is skipped and counted rather than invented. The source ID is the database key: identical repeat imports are unchanged, and corrected contents update that ID. Two different IDs in the same city on the same day remain two reports.

"The client has bounded retries, timeouts and a response-size limit. Downloading finishes before saving. All saves share a transaction, so a database failure rolls them back. If downloading fails, previous data is still there. This summary shows the actual outcome of my import."

### 3:30-5:30 - Swagger UI demonstration

**Show:** `http://127.0.0.1:8000/docs`. Expand the named GET row, click **Try it out**, enter the values below and click **Execute**. Read the **Server response** status and **Response body**, not the illustrative **Example Value** below it. HTTP 200 means the request succeeded, not that a report estimates real-world risk. Collapse each completed route to keep the screen clear. Practise this section; the timings are a guide, not a reason to rush unreadable results.

1. Expand **`GET /`**, click **Try it out**, then **Execute**; no parameters:

   "The root returns a short introduction and the documentation link. This is a JSON API, not a graphical homepage."

2. Expand **`GET /health`**, click **Try it out**, then **Execute**; no parameters:

   "The 200 response shows that the backend can access its local database and count rows. It does not check whether Elanco is online or the snapshot is fresh."

3. Expand **`GET /sightings`**, click **Try it out**, enter `limit=3`, `offset=0`, leave filters blank, then **Execute**:

   "This returns a page of normalised records plus the total number matching. Results have a stable date-and-ID order, and the page size is bounded."

4. Keep **`GET /sightings`** open. Enter `location=London` and leave dates blank; click **Execute**. Then add `start_date=2024-01-01`, `end_date=2024-12-31` and click **Execute** again:

   "The filters can be combined. Location is a literal case-insensitive substring and both date boundaries are inclusive. A valid search with no matches returns an empty list, not an error. The inspected source covers 2012 to 2024, so a 2026 search is not a useful live-data demo."

5. Expand **`GET /stats/regions`**, click **Try it out**, leave filters blank and click **Execute**:

   "The required route is called regions, but the source only supplies cities. I make that limitation explicit with grouped_by location and a note, rather than inventing administrative regions. Each count is a number of stored reports."

6. Expand **`GET /stats/trends`**, click **Try it out**, leave filters blank, choose `period=month` and click **Execute**. Change the same dropdown to `period=week` and click **Execute** again:

   "Monthly buckets start on day one; weekly buckets start on Monday, including across year boundaries. These reports return only buckets containing records. The same location and date filters are available, and a filtered bucket may be only part of a week or month."

### 5:30-6:30 - Error handling and tests

**Show:** expand `/sightings`, click **Try it out** if needed, clear `location`, enter `start_date=2024-12-31`, `end_date=2024-01-01` and click **Execute**. Point to the actual **422** server response. Then show the test terminal and run `.\.venv\Scripts\python.exe -m pytest -q`.

"Here the end date is before the start date. The API returns a useful 422 validation response instead of running a misleading search. Invalid page sizes and dates are rejected too. A local database failure gets a safe 503 message, without exposing its path.

"These are the tests I just ran. They use synthetic fixtures and isolated databases. They cover repeated imports, corrected records, missing data, upstream failures, literal search text, date boundaries, pagination, and weekly or monthly counts. There is one documented upstream test-client deprecation warning; I have not hidden it. The live verifier separately checks the running HTTP API, and I also checked that Swagger actually renders."

### 6:30-7:30 - Design decisions and conclusion

**Show:** architecture limitations and checklist.

"The core backend can import, search and report on the supplied dataset, with repeatable imports and tested failure handling. The main limitations are that the source is unpaginated and only provides cities. With more time, I would add clearer skip-reason reports, a reviewed city-to-region mapping and source-supported pagination. Authentication and higher-concurrency storage would matter before public deployment. The repository contains the setup steps, tests and these decisions so the project can be reviewed and run locally. Thank you."

## Record and save on Windows

1. Show only the project in VS Code and the local Swagger browser. Close unrelated tabs, hide email/credentials and pause notifications. Keep the recording area over those windows, not private desktop files.
2. Open **Snipping Tool**, select **Record**, then **New** (or use `Win+Shift+R` where supported). Select the screen area containing the editor/browser. Before starting, enable the microphone control and select/check the intended microphone if offered. Tool versions vary, so make a 15-second test and listen to the saved playback; do not assume narration was captured. Microsoft documents [recording controls](https://support.microsoft.com/en-gb/windows/apps/use-snipping-tool-to-capture-screenshots?nochrome=true) and the [microphone toggle](https://www.microsoft.com/en-us/windows/learning-center/how-to-use-snipping-tool-on-windows-screenshots-shortcuts-and-screen-recordings).
3. Select **Start**, deliver the prepared demonstration, then **Stop**. Save or use **Save as** if offered; check `Videos\Screen Recordings` if automatic saving is enabled. Choose a sensible filename such as `Hafiz-Furqan-FAISEL-Elanco-Backend.mp4` and locate the actual file before sharing it.
4. If the installed recorder has no working microphone option, use another already-installed recorder with microphone capture rather than submitting a silent video. Xbox Game Bar (`Win+G`) can record supported app windows but may not suit switching between editor and browser. Do not install or configure another service merely for this task.
5. Play the final file from beginning to end. Check narration, legible text, no personal information, all demonstrated responses, and a duration **no longer than 10 minutes** in the player's timeline/properties. Retain the local original.

## Share an unlisted YouTube link, if desired

Do these steps yourself after reviewing the finished video. No upload, account action or email is performed by the project.

1. Sign in to **YouTube Studio**, choose **Create > Upload videos** and select the actual file. Give it a clear project title and answer the required audience/details questions truthfully. Follow [YouTube's upload instructions](https://support.google.com/youtube/answer/57407?hl=en).
2. On **Visibility**, choose **Unlisted**, not Public or Private, and save the choice. For an existing upload, open **Content**, find the video and update its **Visibility**. An unlisted link is viewable and reshareable by anyone who has it; it is not a confidential file. See [YouTube's visibility guidance](https://support.google.com/youtube/answer/157177?hl=en).
3. Wait for processing to finish, copy the actual video URL and open it in a signed-out/private browser window. Play it, check audio and length, and confirm that no special account invitation is needed.
4. Put that verified URL in `SUBMISSION_CHECKLIST.md` and the email draft. Alternatively use the video-file submission method accepted by the brief. Do not replace the placeholder with an invented link or mark recording complete because this script exists.
