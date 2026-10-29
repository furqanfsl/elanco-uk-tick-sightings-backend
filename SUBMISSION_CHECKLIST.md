# Submission checklist

**Deadline: Sunday 1 November 2026, 09:00 UK time.** Plan to finish before the deadline, especially given Friday/Saturday availability. The placement interview is Thursday 29 October. A working backend is not the same as a completed submission: the video and sending the email remain human actions. Public publication was approved on 28 October 2026. The name below matches the candidate's GitHub profile; confirm the preferred submission spelling before sending.

## Latest local review — 29 October 2026

- [x] Reinspect the live source and repeat ingestion: two imports each returned 1,000 unchanged, with zero inserts, updates, skips or errors.
- [x] Start the stopped backend using the README command; all eight documented GET URLs returned HTTP 200 and the verifier passed 24 checks, 0 skipped.
- [x] Run the expanded deterministic suite: **123 passed, 0 failed**, with one known upstream warning; dependency consistency and compilation passed.
- [x] Independently reconcile database rows, filtering, pagination and city/week/month report counts.
- [x] Recheck desktop/mobile Swagger rendering and actual 200/422 interactions; before/after screenshots inspected, eight scoped axe states reported zero violations. Existing mobile JSON density/manual-review limitations remain.
- [x] Review the five submission documents, fix the README heading and add observed JSON response examples.
- [x] Confirm the existing GitHub repository still responds anonymously and is public.
- [x] Reproduce a clean Windows install: public `e0efd7f` passed 119 tests; the hash-verified intended source snapshot passed 123, each with 0 failures/skips and the documented warning. The fresh server created an empty database automatically; first real ingestion inserted 1,000 and repeat ingestion found 1,000 unchanged. Populated verifier: 24 passed; independent clean-install harness: 44 passed.
- [x] Recheck publication safety: 28 tracked files and 45 historical blobs had no checked known credential/private-key pattern hits; private/generated paths remain ignored. All 24 installed project-environment packages had no known vulnerabilities reported by the fresh-cache dependency audit. These checks are not an absolute security guarantee.
- [x] Keep downloaded source records and the generated database out of Git. No explicit dataset redistribution permission was established from the inspected upstream documentation/OpenAPI; public access alone is not permission to redistribute.
- [ ] Review, commit and push this recheck's local README/checklist/test changes; then recheck the remote revision and signed-out access. No commit or push was performed during this recheck. The publication and clean-clone checks below describe the 28 October revision.
- [ ] Complete the recording, preferred-name confirmation and final submission actions below before the deadline.

## Requirement review

The following evidence was observed on 28 October 2026. Automated verification independently rerun during this documentation review: **119 tests passed, 0 failed, 0 skipped**, with one documented upstream Starlette test-client deprecation warning. See the README's dated launch record for the latest installation, browser and running-server checks; subsequent changes require a recheck.

| Requirement | Implementation | Test evidence | Status |
|---|---|---|---|
| Data handling | `app/client.py:fetch_sightings`, `app/processing.py:normalize_record`, `scripts/import_sightings.py:import_sightings` | `test_processing.py`, mocked import/HTTP tests; actual source inspection and import | Verified; the initial import inserted 1,000. This audit's two repeat imports each retrieved 1,000, found 1,000 unchanged and inserted/updated/skipped 0 |
| Duplicates | `app/database.py:save_sightings` with the `source_id` primary key | `test_import.py:test_repeat_import_does_not_duplicate_distinct_same_day_reports`, `test_changed_source_id_updates_existing_record`; repeated real imports | Verified; distinct IDs on the same date/city are retained |
| Missing data | `app/processing.py:normalize_record` and `clean_text` | `test_processing.py`; `test_import.py:test_malformed_records_are_skipped_but_missing_optional_location_is_kept` | Verified with synthetic missing/malformed rows; essential ID/date failures skip, optional text becomes null |
| Date filtering | `GET /sightings`, `app/main.py:get_filters`, `app/database.py:get_sightings` | `test_api.py:test_inclusive_date_filter`, invalid-range tests; database start/end/shared-filter tests | Verified; inclusive valid calendar dates |
| Location filtering | `GET /sightings`, `app/database.py:_filters` | `test_api.py:test_literal_case_insensitive_location`; `test_database.py:test_search_is_literal_and_parameterised` | Verified; literal substring using SQLite lowercasing, sufficient for the inspected ASCII cities |
| Regional/location reporting | `GET /stats/regions`, `app/database.py:count_sightings_by_region` | `test_api.py:test_regions_are_honest_city_counts`; `test_database.py:test_missing_location_is_reported_without_inventing_one`, `test_region_counts_use_locations_and_shared_filters` | Verified city-level aggregation; administrative regions unavailable in source, explicitly disclosed |
| Weekly/monthly trends | `GET /stats/trends`, `app/database.py:get_trends` | `test_api.py:test_weekly_trends_across_year`, `test_monthly_trends`; database Monday/Sunday/year-boundary and filtered-bucket tests | Verified |
| Error handling | Bounded HTTP retries/size, source errors, skipped rows, transactional saves, 422 validation and safe 503 responses | `test_import.py:test_failed_refresh_preserves_previous_import`, retry/timeout/JSON tests; `test_database.py:test_save_rolls_back_partial_changes`; `test_api.py:test_database_failure_is_safe`, invalid-query tests | Verified |

### Backend and documentation

- [x] Old project safely preserved at `D:\First_Project`; its existing GitHub backup branch was reverified, not recreated.
- [x] Elanco project uses the separate `furqanfsl/elanco-uk-tick-sightings-backend` repository, not the old project's remote.
- [x] All four Backend core areas addressed: data handling, search/filtering, reporting and error handling.
- [x] Application starts locally using the README's Uvicorn command.
- [x] Swagger UI works at `http://127.0.0.1:8000/docs`; port 5500 static-file listing is not the backend.
- [x] External Elanco API inspected; actual endpoint/schema and limitations documented.
- [x] Elanco data integration implemented through the HTTP client and import script.
- [x] Real import verified; educational/unpaginated-data limitations documented.
- [x] Duplicate handling verified with repeat imports and stable-ID correction tests.
- [x] Missing-data handling verified with isolated synthetic fixtures.
- [x] Location filtering works, including the documented case-insensitive/literal behaviour.
- [x] Date filtering works, including either boundary alone and inclusive combined ranges.
- [x] Valid empty results work without inventing records.
- [x] City-level statistics work without pretending cities are administrative regions.
- [x] Weekly trends work with Monday/week/year-boundary checks.
- [x] Monthly trends work with first-of-month/calendar ordering checks.
- [x] Error handling and failed-refresh preservation tested.
- [x] Automated tests pass using isolated synthetic fixtures, without requiring Elanco access.
- [x] Running-server verifier executed after restart: 24 checks passed, 0 skipped.
- [x] Swagger rendered and success/422 interactions checked in desktop/mobile headless Edge; final before/after visual evidence and scoped accessibility checks are recorded in README.
- [x] README includes setup, commands, limitations, decisions and actual launch evidence.
- [x] Architecture document is complete and matches the implementation.
- [x] Interview guide includes file/function inputs and outputs, a concept glossary, 20 questions and five-minute revision notes.
- [x] Video walkthrough script is complete; recording is a separate unchecked action below.

### Before publishing

- [x] Add the name from the candidate's GitHub profile to the README, video script and email draft: Hafiz Furqan FAISEL.
- [ ] Confirm that Hafiz Furqan FAISEL is the preferred name and spelling for the final submission.
- [x] Review the files and rerun tests after changes: 119 passed in the current environment and a fresh anonymous public-clone installation; 0 failed and 0 skipped in each.
- [x] Confirm the final README launch record contains no outstanding verification items.
- [x] Approve making `elanco-uk-tick-sightings-backend` public (explicit approval received 28 October 2026).
- [x] GitHub repository created and verified public with the user's approval.
- [x] GitHub URL verified: https://github.com/furqanfsl/elanco-uk-tick-sightings-backend
- [x] After this audit's changes were pushed, verify the public remote `main` revision matches the local commit; recheck again after any subsequent change.
- [x] Verify signed-out access: anonymous HTTP/source requests, a fresh browser context on desktop/mobile, and an anonymous Git clone all succeeded.
- [x] Previously published file list reviewed: no `.venv`, `.env`, database, downloaded raw dataset, caches, personal notes or credentials; `data/` contains only `.gitkeep`.
- [x] Recheck the uploaded file list after adding the shared task configuration: 28 intended files match the local tracked list; only `.vscode/tasks.json` is shared. Personal `.vscode/settings.json`, `memory.md`, local data, environments and caches remain excluded.

### Video and final submission

- [ ] Record the walkthrough using `VIDEO_WALKTHROUGH.md` as a guide.
- [ ] Watch the complete video and confirm clear audio/readable text.
- [ ] Confirm duration is no longer than 10 minutes.
- [ ] Include the actual video file or a verified accessible video link.
- [x] Candidate's full name is included in the prepared README, speaking script and email draft, using the GitHub-profile spelling.
- [x] Short final email draft prepared below; **not sent**.
- [ ] Replace all email placeholders and verify both links/attachments.
- [ ] Send before **09:00 UK time on 1 November 2026**.
- [ ] Check the sent message and keep the submission confirmation.

## Email draft - review and send manually

**To:** BECKY.MEARS@network.elancoah.com

**Subject:** Elanco Software Engineering Placement 2026 – Backend Technical Task Submission

Dear Becky,

I selected the Backend task for the Elanco Software Engineering Placement 2026. Please find my submission below.

- Candidate: Hafiz Furqan FAISEL
- Public GitHub repository: https://github.com/furqanfsl/elanco-uk-tick-sightings-backend
- Walkthrough video: [VERIFIED VIDEO LINK OR ATTACHED FILENAME]

The README includes instructions for running the application and tests, together with the main technical choices and limitations.

Thank you for considering my application.

Kind regards,

Hafiz Furqan FAISEL

**This is a draft only. No email or video submission has been sent automatically.**
