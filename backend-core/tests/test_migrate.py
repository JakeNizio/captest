from backend_core.db import to_sqlalchemy_url
from backend_core.migrate import alembic_config, PACKAGE_ROOT


def test_to_sqlalchemy_url_uses_psycopg_driver():
    assert (
        to_sqlalchemy_url("postgresql://user:pass@localhost:5432/db")
        == "postgresql+psycopg://user:pass@localhost:5432/db"
    )


def test_alembic_config_points_at_package_files():
    cfg = alembic_config("postgresql://platform_admin:x@localhost:5432/core_platform")
    assert (PACKAGE_ROOT / "alembic.ini").is_file()
    assert (PACKAGE_ROOT / "alembic" / "versions" / "0001_initial_schema.py").is_file()
    assert cfg.get_main_option("script_location") == str(PACKAGE_ROOT / "alembic")
    assert cfg.get_main_option("sqlalchemy.url").startswith("postgresql+psycopg://")
