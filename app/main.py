"""Read-only HTTP routes. Importing data is a separate local command."""
import logging
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

from app import database
from app.config import Settings, get_settings
from app.models import HealthResponse, RegionalReport, SightingsPage, TrendReport

logger = logging.getLogger(__name__)
DateQuery = Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}-\d{2}$", description="Inclusive calendar date, YYYY-MM-DD.")]
LocationQuery = Annotated[str | None, Query(min_length=1, max_length=200, description="Literal, case-insensitive substring of the city name.")]


def get_filters(location: LocationQuery = None, start_date: DateQuery = None, end_date: DateQuery = None) -> dict:
    for value in (start_date, end_date):
        if value is not None:
            try:
                date.fromisoformat(value)
            except ValueError:
                raise HTTPException(422, "Dates must be valid calendar dates in YYYY-MM-DD format.") from None
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, "end_date must be on or after start_date.")
    if location is not None:
        location = location.strip()
        if not location:
            raise HTTPException(422, "location must contain a city name or part of one.")
    return {"location": location, "start_date": start_date, "end_date": end_date}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        database.init_database(settings.database_path)
        yield

    application = FastAPI(
        title="Elanco UK Tick Sightings Backend",
        version="1.0.0",
        docs_url=None,
        description=(
            "Explore locally imported Elanco placement-task data. This is an educational dataset, "
            "not live tick surveillance or a measure of disease risk. Run the import script first. "
            "Locations are cities; the source does not provide administrative regions."
        ),
        lifespan=lifespan,
    )
    application.state.settings = settings

    @application.get("/docs", include_in_schema=False)
    def documentation():
        page = get_swagger_ui_html(
            openapi_url="/openapi.json", title=application.title + " - Swagger UI",
            swagger_ui_parameters={"deepLinking": False, "syntaxHighlight": False},
        )
        # Keep the standard Swagger UI, but make its pale method badges and links readable.
        style = """<style>
        .swagger-ui .opblock.opblock-get .opblock-summary-method {background:#0063a6}
        .swagger-ui .info a {color:#0063a6}
        .swagger-ui .info .title small {background:#4b5563}
        .swagger-ui .info .title small.version-stamp {background:#426600}
        .swagger-ui :is(.model-hint,.parameter__in,.parameter__extension,.json-schema-2020-12-expand-deep-button) {color:#555}
        .swagger-ui .btn.execute {background:#0063a6;border-color:#0063a6}
        .swagger-ui .btn.cancel {color:#b91c1c;border-color:#b91c1c}
        .swagger-ui .download-contents {background:#4b5563;min-height:44px}
        .swagger-ui .opblock pre {white-space:pre-wrap;overflow-wrap:anywhere;padding-bottom:64px!important}
        .swagger-ui .highlight-code>.microlight {max-height:none;overflow:visible}
        .swagger-ui .copy-to-clipboard, .swagger-ui .copy-to-clipboard button {width:44px;height:44px}
        .swagger-ui :is(.opblock-summary-control,.btn,input,select) {min-height:44px}
        .swagger-ui :is(button,input,select,a):focus-visible {outline:3px solid #0063a6;outline-offset:3px}
        </style>"""
        html = page.body.decode().replace("<html>", '<html lang="en">')
        return HTMLResponse(html.replace("</head>", style + "</head>"))

    @application.exception_handler(sqlite3.Error)
    async def database_error(request: Request, error: sqlite3.Error):
        logger.warning("A local database operation failed (%s).", type(error).__name__)
        return JSONResponse(status_code=503, content={
            "detail": "Local database unavailable. Check its path and permissions, then try again."
        })

    @application.get("/", tags=["Service"], summary="Introduce the backend")
    def home():
        return {
            "message": "Elanco UK Tick Sightings API",
            "description": "Read-only backend for exploring the Elanco educational tick dataset.",
            "documentation": "/docs",
        }

    @application.get("/health", response_model=HealthResponse, tags=["Service"], summary="Check the backend and local database", responses={503: {"description": "Local database unavailable"}})
    def health():
        return HealthResponse(stored_sightings=database.count_all(settings.database_path))

    @application.get("/sightings", response_model=SightingsPage, tags=["Sightings"], summary="Search stored sightings", responses={503: {"description": "Local database unavailable"}})
    def sightings(
        filters: Annotated[dict, Depends(get_filters)],
        limit: Annotated[int, Query(ge=1, le=200, description="Maximum records in this page.")] = 50,
        offset: Annotated[int, Query(ge=0, le=9223372036854775807, description="Records to skip, at most SQLite's signed 64-bit integer maximum.")] = 0,
    ):
        return database.get_sightings(settings.database_path, **filters, limit=limit, offset=offset)

    @application.get("/stats/regions", response_model=RegionalReport, tags=["Reports"], summary="Count sightings by supplied city", responses={503: {"description": "Local database unavailable"}})
    def regions(filters: Annotated[dict, Depends(get_filters)]):
        return RegionalReport(regions=database.count_sightings_by_region(settings.database_path, **filters))

    @application.get("/stats/trends", response_model=TrendReport, tags=["Reports"], summary="Count sightings by week or month", responses={503: {"description": "Local database unavailable"}})
    def trends(
        filters: Annotated[dict, Depends(get_filters)],
        period: Annotated[Literal["week", "month"], Query(description="Calendar weeks start on Monday; months start on day 1.")] = "month",
    ):
        return TrendReport(period=period, trends=database.get_trends(settings.database_path, period=period, **filters))

    return application


app = create_app()
