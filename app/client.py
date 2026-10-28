"""Download the documented, unpaginated Elanco educational dataset."""

import json
import time

import httpx

from app.config import Settings


class SourceError(Exception):
    """A source failure that can be explained without leaking its response."""


def fetch_sightings(settings: Settings, *, transport=None) -> list:
    """Fetch one JSON array, with a size cap and at most three attempts."""
    with httpx.Client(
        timeout=settings.request_timeout,
        transport=transport,
        follow_redirects=False,
        headers={"Accept": "application/json"},
    ) as client:
        for attempt in range(3):
            try:
                with client.stream("GET", settings.source_url) as response:
                    if response.status_code == 429 or response.status_code >= 500:
                        if attempt == 2:
                            raise SourceError(
                                f"Elanco source returned HTTP {response.status_code} after three attempts. Try again later."
                            )
                        delay = 0.5 * (2 ** attempt)
                        if response.status_code == 429 and response.headers.get("Retry-After"):
                            # A long or date-form retry window is left to the user, not ignored.
                            try:
                                retry_after = float(response.headers["Retry-After"])
                            except ValueError:
                                raise SourceError("Elanco source rate limit reached. Wait before trying again.") from None
                            if not 0 <= retry_after <= 2:
                                raise SourceError("Elanco source rate limit reached. Wait before trying again.")
                            delay = max(delay, retry_after)
                    else:
                        if response.status_code != 200:
                            raise SourceError(f"Elanco source returned HTTP {response.status_code}.")
                        body = bytearray()
                        # iter_bytes counts decoded bytes too, so compression cannot bypass the cap.
                        for chunk in response.iter_bytes():
                            if len(body) + len(chunk) > settings.max_response_bytes:
                                raise SourceError("Elanco source response exceeded the size limit.")
                            body.extend(chunk)
                        try:
                            records = json.loads(body)
                        except (ValueError, RecursionError):
                            raise SourceError("Elanco source did not return valid JSON.") from None
                        if not isinstance(records, list):
                            raise SourceError("Elanco source must return a JSON array of sightings.")
                        return records
            except httpx.RequestError:
                if attempt == 2:
                    raise SourceError("Elanco source could not be reached after three attempts. Try again later.") from None
                delay = 0.5 * (2 ** attempt)
            time.sleep(delay)
