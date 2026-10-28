"""Small synthetic fixtures: never connect tests to Elanco or the real database."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api(tmp_path):
    from app.config import Settings
    from app.main import create_app

    application = create_app(Settings(database_path=tmp_path / "test.db"))
    with TestClient(application) as client:
        yield client


@pytest.fixture
def populated_api(api):
    from app.database import save_sightings
    from app.models import Sighting

    save_sightings(api.app.state.settings.database_path, [
        Sighting(source_id="synthetic-a", sighting_date="2025-12-28", location="Example City"),
        Sighting(source_id="synthetic-b", sighting_date="2025-12-29", location="Example City", species="Test tick"),
        Sighting(source_id="synthetic-c", sighting_date="2026-01-01", location="Other City"),
        Sighting(source_id="synthetic-d", sighting_date="2026-01-04"),
    ])
    return api
