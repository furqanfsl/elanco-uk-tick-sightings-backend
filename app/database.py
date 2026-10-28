"""SQLite storage and reporting for cleaned sightings."""

import sqlite3
from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path

from app.models import Sighting


@contextmanager
def _connect(path: Path):
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def init_database(path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as connection, connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS sightings (
                source_id TEXT PRIMARY KEY NOT NULL,
                sighting_date TEXT NOT NULL,
                location TEXT,
                species TEXT,
                latin_name TEXT
            )
        """)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_sightings_date ON sightings(sighting_date)"
        )
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_sightings_location_date
            ON sightings(location COLLATE NOCASE, sighting_date)
        """)


def save_sightings(path: Path, records: Iterable[Sighting]) -> dict[str, int]:
    counts = {"inserted": 0, "updated": 0, "unchanged": 0}
    with _connect(path) as connection, connection:
        # One transaction makes repeated imports safe and avoids a disk commit per row.
        connection.execute("BEGIN IMMEDIATE")
        for record in records:
            values = record.model_dump()
            previous = connection.execute(
                "SELECT source_id, sighting_date, location, species, latin_name "
                "FROM sightings WHERE source_id = ?",
                (record.source_id,),
            ).fetchone()
            if previous is None:
                connection.execute("""
                    INSERT INTO sightings (source_id, sighting_date, location, species, latin_name)
                    VALUES (:source_id, :sighting_date, :location, :species, :latin_name)
                """, values)
                counts["inserted"] += 1
            elif dict(previous) == values:
                counts["unchanged"] += 1
            else:
                connection.execute("""
                    UPDATE sightings SET sighting_date = :sighting_date, location = :location,
                        species = :species, latin_name = :latin_name
                    WHERE source_id = :source_id
                """, values)
                counts["updated"] += 1
    return counts


def _filters(location=None, start_date=None, end_date=None):
    clauses = []
    parameters = []
    if location is not None:
        # instr treats %, _ and quotes as ordinary search text, not SQL wildcards.
        clauses.append("instr(lower(location), lower(?)) > 0")
        parameters.append(location)
    if start_date is not None:
        clauses.append("sighting_date >= ?")
        parameters.append(start_date)
    if end_date is not None:
        clauses.append("sighting_date <= ?")
        parameters.append(end_date)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return where, parameters


def count_all(path: Path) -> int:
    with _connect(path) as connection:
        return connection.execute("SELECT COUNT(*) FROM sightings").fetchone()[0]


def get_sightings(
    path: Path, location=None, start_date=None, end_date=None, limit=50, offset=0
) -> dict:
    where, parameters = _filters(location, start_date, end_date)
    with _connect(path) as connection:
        # Keep the count and page from the same snapshot if an import runs alongside us.
        connection.execute("BEGIN")
        total = connection.execute(
            "SELECT COUNT(*) FROM sightings" + where, parameters
        ).fetchone()[0]
        rows = connection.execute(
            "SELECT source_id, sighting_date, location, species, latin_name FROM sightings"
            + where + " ORDER BY sighting_date DESC, source_id ASC LIMIT ? OFFSET ?",
            [*parameters, limit, offset],
        ).fetchall()
    return {"items": [dict(row) for row in rows], "total": total, "limit": limit, "offset": offset}


def count_sightings_by_region(
    path: Path, location=None, start_date=None, end_date=None
) -> list[dict]:
    where, parameters = _filters(location, start_date, end_date)
    with _connect(path) as connection:
        # The source only supplies cities; these are location groups, not inferred regions.
        rows = connection.execute(
            "SELECT location AS region, COUNT(*) AS count FROM sightings" + where
            + " GROUP BY location ORDER BY count DESC, location ASC", parameters,
        ).fetchall()
    return [dict(row) for row in rows]


def get_trends(
    path: Path, period="month", location=None, start_date=None, end_date=None
) -> list[dict]:
    if period == "month":
        period_expression = "substr(sighting_date, 1, 7) || '-01'"
    elif period == "week":
        # SQLite's weekday is Sunday=0. Shift it so Monday starts every calendar week.
        period_expression = (
            "date(sighting_date, '-' || "
            "((CAST(strftime('%w', sighting_date) AS INTEGER) + 6) % 7) || ' days')"
        )
    else:
        raise ValueError("The trend period must be week or month.")
    where, parameters = _filters(location, start_date, end_date)
    with _connect(path) as connection:
        rows = connection.execute(
            f"SELECT {period_expression} AS period_start, COUNT(*) AS count FROM sightings"
            + where + " GROUP BY period_start ORDER BY period_start ASC", parameters,
        ).fetchall()
    return [dict(row) for row in rows]
