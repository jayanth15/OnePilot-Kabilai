import os
from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel import inspect

DB_DIR = Path(__file__).resolve().parents[2] / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)

_DB_PATH = os.environ.get("KABILAI_DB_PATH", str(DB_DIR / "kabilai.db"))
DATABASE_URL = f"sqlite:///{_DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Additive ALTER TABLE migrations: (table, column, "ADD COLUMN clause").
# These never drop/recreate data, so existing rows are preserved.
_ADDITIVE_COLUMNS: list[tuple[str, str, str]] = [
    ("user", "role", "TEXT NOT NULL DEFAULT 'user'"),
    ("user", "created_at", "DATETIME"),
]


def _additive_migrate() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    for table, column, definition in _ADDITIVE_COLUMNS:
        if table not in existing_tables:
            continue
        columns = {c["name"] for c in inspector.get_columns(table)}
        if column in columns:
            continue
        with engine.begin() as conn:
            conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _additive_migrate()


def get_session():
    with Session(engine) as session:
        yield session
