import os
from pathlib import Path

from sqlalchemy import inspect as sa_inspect
from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

DB_DIR = Path(__file__).resolve().parents[2] / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)


def _build_engine():
    """Use Postgres when prod_db=True (via DATABASE_URL), else local SQLite."""
    if settings.prod_db:
        url = settings.database_url or os.environ.get("DATABASE_URL", "")
        if not url:
            # DATABASE_URL not available (e.g. at build time) — fall back to SQLite
            # so the app can still import/start locally. Point it at the local file.
            return create_engine(
                f"sqlite:///{os.environ.get('KABILAI_DB_PATH', str(DB_DIR / 'kabilai.db'))}",
                connect_args={"check_same_thread": False},
            )
        # Use the psycopg (v3) dialect if no explicit dialect is provided.
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1).replace(
                "postgres://", "postgresql+psycopg://", 1
            )
        return create_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=20)

    _db_path = os.environ.get("KABILAI_DB_PATH", str(DB_DIR / "kabilai.db"))
    url = f"sqlite:///{_db_path}"
    return create_engine(url, connect_args={"check_same_thread": False})


engine = _build_engine()

# Additive ALTER TABLE migrations: (table, column, "ADD COLUMN clause").
# These never drop/recreate data, so existing rows are preserved.
_ADDITIVE_COLUMNS: list[tuple[str, str, str]] = [
    ("user", "role", "VARCHAR(255) NOT NULL DEFAULT 'user'"),
    ("user", "created_at", "TIMESTAMP"),
]


def _additive_migrate() -> None:
    inspector = sa_inspect(engine)
    existing_tables = set(inspector.get_table_names())
    for table, column, definition in _ADDITIVE_COLUMNS:
        if table not in existing_tables:
            continue
        columns = {c["name"] for c in inspector.get_columns(table)}
        if column in columns:
            continue
        with engine.begin() as conn:
            conn.exec_driver_sql(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {definition}')


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _additive_migrate()


def get_session():
    with Session(engine) as session:
        yield session
