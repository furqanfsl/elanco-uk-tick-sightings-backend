"""Inspect structure and missing fields without dumping source sightings."""

import json
import sys

from app.client import SourceError, fetch_sightings
from app.config import Settings, get_settings


def inspect_api(settings: Settings | None = None, *, transport=None) -> dict:
    settings = settings if settings is not None else get_settings()
    records = fetch_sightings(settings, transport=transport)
    objects = [record for record in records if isinstance(record, dict)]
    fields = sorted({key for record in objects for key in record})
    return {
        "top_level": "array",
        "records": len(records),
        "non_object_records": len(records) - len(objects),
        "field_types": {
            field: sorted({type(record[field]).__name__ for record in objects if field in record})
            for field in fields
        },
        "missing_or_blank": {
            field: sum(record.get(field) is None or record.get(field) == "" for record in objects)
            for field in ["id", "date", "location", "species", "latinName"]
        },
        "pagination": "No pagination is documented for the inspected source endpoint.",
        "data_note": "Elanco labels this an educational placement dataset, not live surveillance.",
    }


def main() -> int:
    try:
        summary = inspect_api()
    except (SourceError, ValueError) as error:
        print(f"Inspection failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
