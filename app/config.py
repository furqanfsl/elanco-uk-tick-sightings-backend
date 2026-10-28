"""Small, environment-based settings shared by the API and import scripts."""
import math
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    source_url: str = "https://dev-task.elancoapps.com/data/tick-sightings"
    database_path: Path = PROJECT_ROOT / "data" / "sightings.db"
    request_timeout: float = 10.0
    max_response_bytes: int = 5 * 1024 * 1024

    def __post_init__(self):
        try:
            url = urlsplit(self.source_url)
            # Reading .port also validates its numeric value and range.
            _ = url.port
        except ValueError:
            raise ValueError("ELANCO_SOURCE_URL must be a valid HTTPS URL without credentials.") from None
        if (url.scheme != "https" or not url.hostname or url.username or url.password
                or any(character.isspace() for character in self.source_url)):
            raise ValueError("ELANCO_SOURCE_URL must be a valid HTTPS URL without credentials.")
        if not math.isfinite(self.request_timeout) or not 0 < self.request_timeout <= 60:
            raise ValueError("ELANCO_REQUEST_TIMEOUT must be between 0 and 60 seconds.")
        if not 0 < self.max_response_bytes <= 50 * 1024 * 1024:
            raise ValueError("ELANCO_MAX_RESPONSE_BYTES must be between 1 and 52428800.")


def get_settings() -> Settings:
    path = Path(os.environ.get("ELANCO_DATABASE_PATH", "data/sightings.db"))
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return Settings(
        source_url=os.environ.get("ELANCO_SOURCE_URL", Settings.source_url),
        database_path=path,
        request_timeout=float(os.environ.get("ELANCO_REQUEST_TIMEOUT", "10")),
        max_response_bytes=int(os.environ.get("ELANCO_MAX_RESPONSE_BYTES", "5242880")),
    )
