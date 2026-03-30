from sqlalchemy import inspect, text

from db.database import SessionLocal
from db.database import engine
from db.models import Base  # noqa: F401


def get_session():
    return SessionLocal()


def _ensure_order_dataset_schema() -> None:
    inspector = inspect(engine)
    if "order_dataset" not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns("order_dataset")}
    with engine.begin() as conn:
        if "row_hash" not in columns:
            conn.execute(text("ALTER TABLE order_dataset ADD COLUMN row_hash VARCHAR(64)"))
        # Idempotent indexes for dedup + speed.
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_order_dataset_row_hash ON order_dataset(row_hash)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_order_dataset_raw_chat_id ON order_dataset(raw_chat_id)"))


def init_db() -> bool:
    try:
        Base.metadata.create_all(bind=engine)
        _ensure_order_dataset_schema()
        return True
    except Exception:
        return False
