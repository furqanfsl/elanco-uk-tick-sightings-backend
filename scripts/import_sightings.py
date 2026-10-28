"""Run with: python -m scripts.import_sightings"""

import json
import sqlite3
import sys

from app.client import SourceError, fetch_sightings
from app.config import Settings, get_settings
from app.database import init_database, save_sightings
from app.processing import normalize_record


def import_sightings(settings: Settings | None = None, *, transport=None) -> dict:
    settings = settings if settings is not None else get_settings()
    # Fetch before opening a write transaction, so a failed refresh leaves stored data alone.
    records = fetch_sightings(settings, transport=transport)
    valid = []
    skipped = 0
    for record in records:
        try:
            valid.append(normalize_record(record))
        except ValueError:
            skipped += 1

    init_database(settings.database_path)
    saved = save_sightings(settings.database_path, valid)
    return {"retrieved": len(records), **saved, "skipped": skipped, "errors": 0}


def main(settings: Settings | None = None, *, transport=None) -> int:
    try:
        summary = import_sightings(settings, transport=transport)
    except SourceError as error:
        print(f"Import failed: {error} Existing data was not removed.", file=sys.stderr)
        return 1
    except (sqlite3.Error, OSError):
        print("Import failed: the local database could not be written. Check its path and permissions.", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"Import failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
