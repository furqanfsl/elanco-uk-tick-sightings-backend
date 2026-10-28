"""The small JSON contracts used by the application."""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Sighting(BaseModel):
    """Normalised record. All documentation example values are synthetic."""
    source_id: str = Field(min_length=1, max_length=200, examples=["synthetic-example-1"])
    sighting_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["2024-02-29"])
    location: str | None = Field(default=None, max_length=200, examples=["Example City"])
    species: str | None = Field(default=None, max_length=200, examples=["Example tick"])
    latin_name: str | None = Field(default=None, max_length=200, examples=["Example species"])

    @field_validator("sighting_date")
    @classmethod
    def valid_calendar_date(cls, value: str) -> str:
        date.fromisoformat(value)
        return value


class SightingsPage(BaseModel):
    items: list[Sighting]
    total: int
    limit: int
    offset: int


class RegionCount(BaseModel):
    region: str | None
    count: int


class RegionalReport(BaseModel):
    grouped_by: Literal["location"] = "location"
    note: str = "City-level counts: the source has no administrative region field. Null means location was not supplied."
    regions: list[RegionCount]


class TrendCount(BaseModel):
    period_start: str
    count: int


class TrendReport(BaseModel):
    period: Literal["week", "month"]
    note: str = "Weeks start on Monday; months start on day 1. Only buckets containing sightings are returned."
    trends: list[TrendCount]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    database: Literal["ok"] = "ok"
    stored_sightings: int
