"""Turn source records into the few fields needed by the MVP."""

import re
from datetime import date, datetime

from app.models import Sighting


def clean_text(value: object, field: str, *, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text.")
    value = value.strip() if field == "id" else " ".join(value.split())
    if not value:
        if required:
            raise ValueError(f"{field} is required.")
        return None
    if len(value) > 200:
        raise ValueError(f"{field} is too long.")
    return value


def parse_sighting_date(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("date must be an ISO date or timestamp.")
    value = value.strip()
    if len(value) > 64 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T.+)?", value):
        raise ValueError("date must be an ISO date or timestamp.")
    try:
        # The source has no timezone. Keep its written calendar day; do not invent UTC.
        parsed = datetime.fromisoformat(value).date() if "T" in value else date.fromisoformat(value)
    except ValueError:
        raise ValueError("date is not a valid ISO date or timestamp.") from None
    return parsed.isoformat()


def normalize_record(raw: object) -> Sighting:
    if not isinstance(raw, dict):
        raise ValueError("A sighting must be a JSON object.")
    return Sighting(
        source_id=clean_text(raw.get("id"), "id", required=True),
        sighting_date=parse_sighting_date(raw.get("date")),
        location=clean_text(raw.get("location"), "location"),
        species=clean_text(raw.get("species"), "species"),
        latin_name=clean_text(raw.get("latinName"), "latinName"),
    )
