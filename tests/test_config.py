"""Configuration tests do not use a live service."""
import pytest

from app.config import get_settings


def test_default_database_is_relative_to_project_not_shell(monkeypatch, tmp_path):
    monkeypatch.delenv("ELANCO_DATABASE_PATH", raising=False)
    monkeypatch.chdir(tmp_path)
    assert get_settings().database_path.name == "sightings.db"
    assert get_settings().database_path.parent.name == "data"
    assert get_settings().database_path.is_absolute()


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "oops"])
def test_invalid_timeout_rejected(monkeypatch, value):
    monkeypatch.setenv("ELANCO_REQUEST_TIMEOUT", value)
    with pytest.raises(ValueError):
        get_settings()


@pytest.mark.parametrize("url", [
    "http://example.invalid/data", "https://", "https://example.invalid:bad/data",
    "https://exa mple.invalid/data", "https://user:secret@example.invalid/data",
])
def test_source_must_be_a_valid_https_url(monkeypatch, url):
    monkeypatch.setenv("ELANCO_SOURCE_URL", url)
    with pytest.raises(ValueError):
        get_settings()
