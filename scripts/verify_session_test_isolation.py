from __future__ import annotations

from sqlalchemy import create_engine, inspect, text

from session_test_runtime import (
    ensure_session_test_database,
    masked_url,
    resolve_session_test_database,
)


def database_name(url) -> str:
    engine = create_engine(url, pool_pre_ping=True, future=True)
    try:
        with engine.connect() as conn:
            return str(conn.execute(text("SELECT current_database()")).scalar_one())
    finally:
        engine.dispose()


def main() -> int:
    config = resolve_session_test_database()
    ensure_session_test_database(config)

    source_name = database_name(config.source_url)
    admin_name = database_name(config.admin_url)
    test_name = database_name(config.target_url)
    if test_name != config.database_name:
        raise RuntimeError(
            f"DB test salah: expected={config.database_name!r}, actual={test_name!r}"
        )
    if test_name == admin_name:
        raise RuntimeError("DB test dan DB administrasi ternyata sama.")
    if source_name == test_name and not test_name.endswith("_session_test"):
        raise RuntimeError("DB sumber dan DB test ternyata sama.")

    engine = create_engine(config.target_url, pool_pre_ping=True, future=True)
    try:
        inspector = inspect(engine)
        public_tables = sorted(inspector.get_table_names(schema="public"))
        session_schemas = sorted(
            schema
            for schema in inspector.get_schema_names()
            if schema.startswith("extract_session_")
        )
    finally:
        engine.dispose()

    print("[OK] Isolasi database aktif.")
    print(f"Source DB: {source_name}")
    print(f"Admin DB : {admin_name}")
    print(f"Test DB  : {test_name}")
    print(f"URL test : {masked_url(config.target_url)}")
    print(
        "Public   : "
        f"{', '.join(public_tables) if public_tables else '(tidak ada tabel)'}"
    )
    print(f"Session  : {len(session_schemas)} schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
