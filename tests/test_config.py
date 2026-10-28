"""Configuration tests do not use a live service."""
import json
from pathlib import Path

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


def test_vscode_start_task_uses_real_backend_not_live_server():
    root = Path(__file__).resolve().parent.parent
    tasks = json.loads((root / ".vscode" / "tasks.json").read_text())["tasks"]
    start = next(task for task in tasks if task["label"] == "Elanco: Start backend (port 8000)")
    assert start["type"] == "process"
    assert start["args"] == ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    assert start["options"]["cwd"] == "${workspaceFolder}"
    assert start["group"] == {"kind": "build", "isDefault": True}
    assert start["windows"]["command"] == "${workspaceFolder}/.venv/Scripts/python.exe"
    assert start["command"] == "${workspaceFolder}/.venv/bin/python"


def test_vscode_support_tasks_match_documented_commands():
    root = Path(__file__).resolve().parent.parent
    tasks = json.loads((root / ".vscode" / "tasks.json").read_text())["tasks"]
    expected = {
        "Elanco: Import sightings": ["-m", "scripts.import_sightings"],
        "Elanco: Verify local backend": ["-m", "scripts.verify_local"],
        "Elanco: Run tests": ["-m", "pytest", "-q"],
    }
    assert len(tasks) == 4
    for label, args in expected.items():
        task = next(task for task in tasks if task["label"] == label)
        assert task["type"] == "process"
        assert task["args"] == args
        assert task["options"]["cwd"] == "${workspaceFolder}"
        assert task["windows"]["command"] == "${workspaceFolder}/.venv/Scripts/python.exe"
        assert task["command"] == "${workspaceFolder}/.venv/bin/python"
