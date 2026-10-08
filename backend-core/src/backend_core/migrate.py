"""Apply Alembic migrations. Used at process startup and as a CLI."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from backend_core.config import get_settings
from backend_core.db import to_sqlalchemy_url


def find_package_root() -> Path:
    """Locate backend-core root (contains alembic.ini) in editable or image layouts."""
    candidates = [
        Path(__file__)
        .resolve()
        .parents[2],  # src layout: backend-core/src/backend_core/
        Path.cwd(),
        Path("/app/backend-core"),
    ]
    for candidate in candidates:
        if (candidate / "alembic.ini").is_file():
            return candidate
    searched = ", ".join(str(path) for path in candidates)
    raise RuntimeError(f"Could not locate alembic.ini (searched: {searched})")


PACKAGE_ROOT = find_package_root()


def alembic_config(database_url: str | None = None) -> Config:
    settings = get_settings()
    url = to_sqlalchemy_url(database_url or settings.database_url)
    root = find_package_root()
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def run_migrations(database_url: str | None = None) -> None:
    """Upgrade the database to the latest Alembic revision."""
    command.upgrade(alembic_config(database_url), "head")


def main() -> None:
    run_migrations()
    print("Migrations applied (alembic upgrade head).")


if __name__ == "__main__":
    main()
