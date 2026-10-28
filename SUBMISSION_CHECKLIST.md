# Submission checklist

**Deadline: Sunday 1 November 2026, 09:00 UK time.** Plan to finish before the deadline, especially given Friday/Saturday availability. The placement interview is Thursday 29 October. A working backend is not the same as a completed submission: publication approval, full name, video and sending the email remain human actions.

## Requirement review

The following evidence was observed on 28 October 2026. Automated verification independently rerun during this documentation review: **117 tests passed**, with one documented upstream Starlette test-client deprecation warning. See the README's dated launch record for the latest installation, browser and running-server checks; subsequent changes require a recheck.

| Requirement | Implementation | Test evidence | Status |
|---|---|---|---|
| Data handling: consume, clean, missing data and duplicates | `app/client.py:fetch_sightings`, `app/processing.py:normalize_record`, `app/database.py:save_sightings`, `scripts/import_sightings.py:import_sightings` | `test_processing.py`; `test_import.py:test_repeat_import_does_not_duplicate_distinct_same_day_reports`, `test_changed_source_id_updates_existing_record`, `test_malformed_records_are_skipped_but_missing_optional_location_is_kept` | Verified; real import inserted 1,000, repeat found 1,000 unchanged |
| Search and filtering by location/time | `GET /sightings`, `app/main.py:get_filters`, `app/database.py:get_sightings` | `test_api.py:test_inclusive_date_filter`, `test_literal_case_insensitive_location`, `test_sightings_pagination`; database literal-search tests | Verified |
| Regional/location reporting | `GET /stats/regions`, `app/database.py:count_sightings_by_region` | `test_api.py:test_regions_are_honest_city_counts`; `test_database.py:test_missing_location_is_reported_without_inventing_one`, `test_region_counts_use_locations_and_shared_filters` | Verified city-level aggregation; administrative regions unavailable in source, explicitly disclosed |
| Weekly/monthly trends | `GET /stats/trends`, `app/database.py:get_trends` | `test_api.py:test_weekly_trends_across_year`, `test_monthly_trends`; database Monday/Sunday/year-boundary and filtered-bucket tests | Verified |
| Error handling | Bounded HTTP retries/size, source errors, skipped rows, transactional saves, 422 validation and safe 503 responses | `test_import.py:test_failed_refresh_preserves_previous_import`, retry/timeout/JSON tests; `test_database.py:test_save_rolls_back_partial_changes`; `test_api.py:test_database_failure_is_safe`, invalid-query tests | Verified |

### Backend and documentation

- [x] All four Backend core areas addressed: data handling, search/filtering, reporting and error handling.
- [x] Application starts locally using the README's Uvicorn command.
- [x] External import works with the inspected source; educational/unpaginated-data limitations documented.
- [x] Filtering and valid empty results work.
- [x] City-level statistics work without pretending cities are administrative regions.
- [x] Monday-week and calendar-month trends work.
- [x] Error handling and failed-refresh preservation tested.
- [x] Automated tests pass using isolated synthetic fixtures, without requiring Elanco access.
- [x] Running-server verifier executed after restart: 24 checks passed, 0 skipped.
- [x] Swagger rendered and success/422 interactions checked in desktop/mobile headless Edge; final before/after visual evidence and scoped accessibility checks are recorded in README.
- [x] README includes setup, commands, limitations, decisions and actual launch evidence.
- [x] Architecture explanation, video script and interview guide prepared.

### Before publishing

- [ ] Replace `[YOUR FULL NAME]` in README, video script and email with the candidate's confirmed name.
- [x] Review the final files and rerun tests after changes (117 passed on both tested Python runtimes).
- [x] Confirm the final README launch record contains no outstanding verification items.
- [ ] Approve making `elanco-uk-tick-sightings-backend` public. **Approval is still pending; do not assume publication is authorised.**
- [ ] Confirm the public repository exists and contains the final intended commit.
- [ ] Open its GitHub URL in a signed-out/private window and verify README/source access.
- [ ] Confirm no private files were uploaded: no `.venv`, `.env`, database, downloaded raw dataset, caches, personal notes or credentials. `.gitignore` alone is not proof; inspect the actual committed/uploaded file list.

### Video and final submission

- [ ] Record the walkthrough using `VIDEO_WALKTHROUGH.md` as a guide.
- [ ] Watch the complete video and confirm clear audio/readable text.
- [ ] Confirm duration is no longer than 10 minutes.
- [ ] Include the actual video file or a verified accessible video link.
- [ ] Confirm the candidate's full name appears in the final submission.
- [x] Short final email draft prepared below; **not sent**.
- [ ] Replace all email placeholders and verify both links/attachments.
- [ ] Send before **09:00 UK time on 1 November 2026**.
- [ ] Check the sent message and keep the submission confirmation.

## Email draft - review and send manually

**To:** BECKY.MEARS@network.elancoah.com

**Subject:** Software Engineering Placement 2026 - Backend Task - [YOUR FULL NAME]

Dear Becky,

Please find my Backend technical task submission for the Elanco Software Engineering Placement 2026.

- Candidate: [YOUR FULL NAME]
- Public GitHub repository: [VERIFIED PUBLIC REPOSITORY LINK]
- Walkthrough video: [VERIFIED VIDEO LINK OR ATTACHED FILENAME]

The README includes instructions for running the application and tests, together with the main technical choices and limitations.

Thank you for considering my application.

Kind regards,

[YOUR FULL NAME]

**This is a draft only. No email or video submission has been sent automatically.**
