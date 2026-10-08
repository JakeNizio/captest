from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend_core.config import Settings, get_settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def to_sqlalchemy_url(database_url: str) -> str:
    """Convert a libpq URL to the SQLAlchemy psycopg3 dialect URL."""
    if database_url.startswith("postgresql+psycopg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgres://")
    return database_url


def get_engine(settings: Settings | None = None) -> Engine:
    global _engine, _SessionLocal
    settings = settings or get_settings()
    if _engine is None:
        _engine = create_engine(
            to_sqlalchemy_url(settings.database_url),
            pool_pre_ping=True,
        )
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    get_engine(settings)
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one session per request. Callers commit explicitly."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def database_ready(settings: Settings | None = None) -> bool:
    """True when Postgres accepts connections and migrations created `tenants`."""
    try:
        engine = get_engine(settings)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM tenants LIMIT 1"))
        return True
    except Exception:
        return False


def reset_engine() -> None:
    """Drop the cached engine/session factory (startup + tests)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
