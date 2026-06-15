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
        if "batch_row_order" not in columns:
            conn.execute(text("ALTER TABLE order_dataset ADD COLUMN batch_row_order INTEGER"))
        # Idempotent indexes for dedup + speed.
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_order_dataset_row_hash ON order_dataset(row_hash)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_order_dataset_raw_chat_id ON order_dataset(raw_chat_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_order_dataset_batch_row_order ON order_dataset(batch_row_order)"))


def _ensure_stage2_match_audit_schema() -> None:
    inspector = inspect(engine)
    if "stage2_match_audits" not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns("stage2_match_audits")}
    with engine.begin() as conn:
        if "decision_status" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN decision_status VARCHAR(80)"))
        if "policy_reason" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN policy_reason TEXT"))
        if "p_no_match" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN p_no_match FLOAT"))
        if "before_rows_json" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN before_rows_json TEXT"))
        if "after_rows_json" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN after_rows_json TEXT"))
        if "incoming_rows_json" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN incoming_rows_json TEXT"))
        if "candidate_source_rows_json" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN candidate_source_rows_json TEXT"))
        if "proposed_fill_count" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN proposed_fill_count INTEGER"))
        if "incoming_complete_units" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN incoming_complete_units INTEGER"))
        if "duplicate_units" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN duplicate_units INTEGER"))
        if "overflow_units" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN overflow_units INTEGER"))
        if "review_required" not in columns:
            conn.execute(text("ALTER TABLE stage2_match_audits ADD COLUMN review_required BOOLEAN"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stage2_match_audits_raw_chat_id ON stage2_match_audits(raw_chat_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stage2_match_audits_decision_status ON stage2_match_audits(decision_status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stage2_match_audits_review_required ON stage2_match_audits(review_required)"))


def init_db() -> bool:
    try:
        Base.metadata.create_all(bind=engine)
        _ensure_order_dataset_schema()
        _ensure_stage2_match_audit_schema()
        return True
    except Exception:
        return False
