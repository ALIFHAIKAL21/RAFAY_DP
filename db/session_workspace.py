from __future__ import annotations

import io
import json
import os
import re
import uuid
import zipfile
from contextvars import ContextVar
from datetime import date, datetime
from typing import Dict, Iterable, List
from urllib.parse import urlparse

import pandas as pd
from sqlalchemy import event, inspect, text

from db.database import Base, DATABASE_URL, engine

# Register all operational tables in Base.metadata before creating session schemas.
from models.order_dataset import OrderDataset  # noqa: F401
from models.raw_chat import RawChat  # noqa: F401
from models.stage2_match_audit import Stage2MatchAudit  # noqa: F401


SESSION_SCHEMA_PREFIX = "extract_session_"
SESSION_NAME_MAX_LENGTH = 120
_ACTIVE_SESSION_ID: ContextVar[str] = ContextVar("active_extraction_session_id", default="")
_ACTIVE_SCHEMA: ContextVar[str] = ContextVar("active_extraction_session_schema", default="")
_EVENT_INSTALLED = False

MONTH_NAMES = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}

MONTH_IDS = {
    "JAN": 1,
    "JANUARI": 1,
    "JANUARY": 1,
    "FEB": 2,
    "FEBRUARI": 2,
    "FEBUARI": 2,
    "FEBRUARY": 2,
    "MAR": 3,
    "MARET": 3,
    "MARCH": 3,
    "APR": 4,
    "APRIL": 4,
    "MEI": 5,
    "MAY": 5,
    "JUN": 6,
    "JUNI": 6,
    "JUNE": 6,
    "JUL": 7,
    "JULI": 7,
    "JULY": 7,
    "AGU": 8,
    "AGUSTUS": 8,
    "AUG": 8,
    "AUGUST": 8,
    "SEP": 9,
    "SEPT": 9,
    "SEPTEMBER": 9,
    "OKT": 10,
    "OKTOBER": 10,
    "OCT": 10,
    "OCTOBER": 10,
    "NOV": 11,
    "NOVEMBER": 11,
    "DES": 12,
    "DESEMBER": 12,
    "DEC": 12,
    "DECEMBER": 12,
}


def _require_test_database() -> str:
    database_name = urlparse(str(DATABASE_URL)).path.strip("/").split("/")[-1]
    expected_name = str(
        os.getenv("IDP_SESSION_TEST_DB_NAME", "logistic_parser_session_test") or ""
    ).strip()
    if (
        str(os.getenv("IDP_SESSION_TEST_MODE", "") or "").strip().lower()
        not in {"1", "true", "on"}
        or not database_name.endswith("_session_test")
        or database_name != expected_name
    ):
        raise RuntimeError(
            "Session workspace hanya boleh aktif pada database pengujian terisolasi."
        )
    return database_name


TEST_DATABASE_NAME = _require_test_database()


def _schema_for_session(session_id: str | uuid.UUID) -> str:
    parsed = uuid.UUID(str(session_id))
    return f"{SESSION_SCHEMA_PREFIX}{parsed.hex}"


def _validate_schema(schema_name: str) -> str:
    if not re.fullmatch(rf"{SESSION_SCHEMA_PREFIX}[0-9a-f]{{32}}", str(schema_name or "")):
        raise ValueError(f"Schema sesi tidak valid: {schema_name!r}")
    return schema_name


def _quoted_schema(schema_name: str) -> str:
    return f'"{_validate_schema(schema_name)}"'


def install_session_schema_router() -> None:
    global _EVENT_INSTALLED
    if _EVENT_INSTALLED:
        return

    @event.listens_for(engine, "checkout")
    def _set_session_search_path(dbapi_connection, connection_record, connection_proxy):
        del connection_record, connection_proxy
        schema_name = _ACTIVE_SCHEMA.get()
        cursor = dbapi_connection.cursor()
        try:
            if schema_name:
                cursor.execute(
                    f"SET search_path TO {_quoted_schema(schema_name)}, public"
                )
            else:
                cursor.execute("SET search_path TO public")
        finally:
            cursor.close()

    _EVENT_INSTALLED = True


install_session_schema_router()


def init_workspace_registry() -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL search_path TO public"))
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS public.extraction_sessions (
                        id UUID PRIMARY KEY,
                        schema_name VARCHAR(80) NOT NULL UNIQUE,
                        name VARCHAR(120) NOT NULL,
                        name_source VARCHAR(20) NOT NULL DEFAULT 'auto',
                        status VARCHAR(20) NOT NULL DEFAULT 'active',
                        inferred_start_date DATE NULL,
                        inferred_end_date DATE NULL,
                        dominant_month INTEGER NULL,
                        dominant_year INTEGER NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        last_opened_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS ix_extraction_sessions_status_updated
                    ON public.extraction_sessions(status, updated_at DESC)
                    """
                )
            )
        return True
    except Exception:
        return False


def _session_record(row) -> Dict[str, object]:
    mapping = dict(row._mapping)
    for key in ("id",):
        if mapping.get(key) is not None:
            mapping[key] = str(mapping[key])
    for key in ("created_at", "updated_at", "last_opened_at"):
        value = mapping.get(key)
        mapping[key] = value.isoformat(sep=" ") if value else ""
    for key in ("inferred_start_date", "inferred_end_date"):
        value = mapping.get(key)
        mapping[key] = value.isoformat() if value else ""
    mapping["row_count"] = int(mapping.get("row_count", 0) or 0)
    mapping["chat_count"] = int(mapping.get("chat_count", 0) or 0)
    mapping["audit_count"] = int(mapping.get("audit_count", 0) or 0)
    return mapping


def _fetch_session(session_id: str | uuid.UUID) -> Dict[str, object] | None:
    try:
        parsed = uuid.UUID(str(session_id))
    except Exception:
        return None
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, schema_name, name, name_source, status,
                       inferred_start_date, inferred_end_date,
                       dominant_month, dominant_year,
                       created_at, updated_at, last_opened_at
                FROM public.extraction_sessions
                WHERE id = :session_id
                """
            ),
            {"session_id": parsed},
        ).first()
    return _session_record(row) if row else None


def _schema_counts(conn, schema_name: str) -> tuple[int, int, int]:
    quoted = _quoted_schema(schema_name)
    row_count = conn.execute(text(f"SELECT COUNT(*) FROM {quoted}.order_dataset")).scalar_one()
    chat_count = conn.execute(text(f"SELECT COUNT(*) FROM {quoted}.raw_chats")).scalar_one()
    audit_count = conn.execute(
        text(f"SELECT COUNT(*) FROM {quoted}.stage2_match_audits")
    ).scalar_one()
    return int(row_count), int(chat_count), int(audit_count)


def list_extraction_sessions(include_archived: bool = False) -> List[Dict[str, object]]:
    init_workspace_registry()
    where_clause = "" if include_archived else "WHERE status = 'active'"
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"""
                SELECT id, schema_name, name, name_source, status,
                       inferred_start_date, inferred_end_date,
                       dominant_month, dominant_year,
                       created_at, updated_at, last_opened_at
                FROM public.extraction_sessions
                {where_clause}
                ORDER BY last_opened_at DESC, updated_at DESC, created_at DESC
                """
            )
        ).all()

        result = []
        for row in rows:
            record = _session_record(row)
            try:
                counts = _schema_counts(conn, str(record["schema_name"]))
            except Exception:
                counts = (0, 0, 0)
            record["row_count"], record["chat_count"], record["audit_count"] = counts
            result.append(record)
    return result


def _next_default_name() -> str:
    with engine.connect() as conn:
        count = int(
            conn.execute(
                text("SELECT COUNT(*) FROM public.extraction_sessions")
            ).scalar_one()
            or 0
        )
    return "Sesi Baru" if count == 0 else f"Sesi Baru {count + 1}"


def _create_session_in_connection(conn, name: str = "") -> str:
    session_id = uuid.uuid4()
    schema_name = _schema_for_session(session_id)
    clean_name = re.sub(r"\s+", " ", str(name or "").strip())[:SESSION_NAME_MAX_LENGTH]
    name_source = "manual" if clean_name else "auto"
    clean_name = clean_name or _next_default_name()

    conn.execute(text(f"CREATE SCHEMA {_quoted_schema(schema_name)}"))
    conn.execute(
        text(
            """
            INSERT INTO public.extraction_sessions (
                id, schema_name, name, name_source, status
            ) VALUES (
                :session_id, :schema_name, :name, :name_source, 'active'
            )
            """
        ),
        {
            "session_id": session_id,
            "schema_name": schema_name,
            "name": clean_name,
            "name_source": name_source,
        },
    )
    return str(session_id)


def create_extraction_session(name: str = "") -> Dict[str, object]:
    init_workspace_registry()
    with engine.begin() as conn:
        session_id = _create_session_in_connection(conn, name)

    set_active_extraction_session(session_id)
    init_active_session_schema()
    return get_active_extraction_session()


def ensure_default_extraction_session(
    preferred_session_id: str = "",
) -> Dict[str, object]:
    init_workspace_registry()
    preferred = _fetch_session(preferred_session_id) if preferred_session_id else None
    if preferred and preferred.get("status") == "active":
        set_active_extraction_session(str(preferred["id"]))
        init_active_session_schema()
        return get_active_extraction_session()

    with engine.begin() as conn:
        conn.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtext('idp_session_workspace_bootstrap'))"
            )
        )
        row = conn.execute(
            text(
                """
                SELECT id
                FROM public.extraction_sessions
                WHERE status = 'active'
                ORDER BY last_opened_at DESC, updated_at DESC, created_at DESC
                LIMIT 1
                """
            )
        ).first()
        session_id = str(row.id) if row else _create_session_in_connection(conn)

    set_active_extraction_session(session_id)
    init_active_session_schema()
    return get_active_extraction_session()


def set_active_extraction_session(session_id: str | uuid.UUID) -> Dict[str, object]:
    record = _fetch_session(session_id)
    if not record:
        raise KeyError(f"Sesi tidak ditemukan: {session_id}")
    if record.get("status") != "active":
        raise ValueError("Sesi diarsipkan dan tidak dapat dijadikan sesi aktif.")

    schema_name = _validate_schema(str(record["schema_name"]))
    _ACTIVE_SESSION_ID.set(str(record["id"]))
    _ACTIVE_SCHEMA.set(schema_name)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE public.extraction_sessions
                SET last_opened_at = CURRENT_TIMESTAMP
                WHERE id = :session_id
                """
            ),
            {"session_id": uuid.UUID(str(record["id"]))},
        )
    return record


def get_active_extraction_session_id() -> str:
    return _ACTIVE_SESSION_ID.get()


def get_active_extraction_session() -> Dict[str, object]:
    session_id = get_active_extraction_session_id()
    if not session_id:
        return {}
    record = _fetch_session(session_id) or {}
    if record:
        schema_name = str(record.get("schema_name", ""))
        try:
            with engine.connect() as conn:
                counts = _schema_counts(conn, schema_name)
        except Exception:
            counts = (0, 0, 0)
        record["row_count"], record["chat_count"], record["audit_count"] = counts
    return record


def init_active_session_schema() -> bool:
    schema_name = _ACTIVE_SCHEMA.get()
    if not schema_name:
        return False
    schema_name = _validate_schema(schema_name)
    try:
        with engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {_quoted_schema(schema_name)}"))
            schema_conn = conn.execution_options(schema_translate_map={None: schema_name})
            Base.metadata.create_all(bind=schema_conn)
        inspector = inspect(engine)
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO {_quoted_schema(schema_name)}, public"))
            tables = set(inspector.get_table_names(schema=schema_name))
        return {"raw_chats", "order_dataset", "stage2_match_audits"}.issubset(tables)
    except Exception:
        return False


def touch_active_extraction_session() -> None:
    session_id = get_active_extraction_session_id()
    if not session_id:
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE public.extraction_sessions
                SET updated_at = CURRENT_TIMESTAMP,
                    last_opened_at = CURRENT_TIMESTAMP
                WHERE id = :session_id
                """
            ),
            {"session_id": uuid.UUID(session_id)},
        )


def rename_extraction_session(session_id: str, name: str) -> Dict[str, object]:
    clean_name = re.sub(r"\s+", " ", str(name or "").strip())[:SESSION_NAME_MAX_LENGTH]
    if not clean_name:
        raise ValueError("Nama sesi tidak boleh kosong.")
    parsed = uuid.UUID(str(session_id))
    with engine.begin() as conn:
        updated = conn.execute(
            text(
                """
                UPDATE public.extraction_sessions
                SET name = :name,
                    name_source = 'manual',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :session_id
                """
            ),
            {"session_id": parsed, "name": clean_name},
        ).rowcount
    if not updated:
        raise KeyError(f"Sesi tidak ditemukan: {session_id}")
    return _fetch_session(session_id) or {}


def archive_extraction_session(session_id: str) -> None:
    parsed = uuid.UUID(str(session_id))
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE public.extraction_sessions
                SET status = 'archived',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :session_id
                """
            ),
            {"session_id": parsed},
        )


def restore_extraction_session(session_id: str) -> None:
    parsed = uuid.UUID(str(session_id))
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE public.extraction_sessions
                SET status = 'active',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :session_id
                """
            ),
            {"session_id": parsed},
        )


def delete_extraction_session(session_id: str) -> None:
    record = _fetch_session(session_id)
    if not record:
        return
    schema_name = _validate_schema(str(record["schema_name"]))
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL search_path TO public"))
        conn.execute(text(f"DROP SCHEMA IF EXISTS {_quoted_schema(schema_name)} CASCADE"))
        conn.execute(
            text("DELETE FROM public.extraction_sessions WHERE id = :session_id"),
            {"session_id": uuid.UUID(str(session_id))},
        )
    if get_active_extraction_session_id() == str(session_id):
        _ACTIVE_SESSION_ID.set("")
        _ACTIVE_SCHEMA.set("")


def _date_from_value(value: str) -> date | None:
    source = str(value or "").strip().upper()
    if not source:
        return None

    numeric = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", source)
    if numeric:
        day, month, year = (int(item) for item in numeric.groups())
        if year < 100:
            year += 2000
        try:
            return date(year, month, day)
        except ValueError:
            return None

    word = re.search(r"\b(\d{1,2})\s+([A-Z]+)\s+(\d{2,4})\b", source)
    if word:
        day = int(word.group(1))
        month = MONTH_IDS.get(word.group(2))
        year = int(word.group(3))
        if year < 100:
            year += 2000
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                return None
    return None


def build_automatic_session_name(values: Iterable[str]) -> Dict[str, object]:
    parsed_dates = sorted(
        item for item in (_date_from_value(value) for value in values) if item is not None
    )
    if not parsed_dates:
        return {}

    start_date = parsed_dates[0]
    end_date = parsed_dates[-1]
    month_year_counts: Dict[tuple[int, int], int] = {}
    for item in parsed_dates:
        key = (item.year, item.month)
        month_year_counts[key] = month_year_counts.get(key, 0) + 1
    dominant_year, dominant_month = max(
        month_year_counts,
        key=lambda key: (month_year_counts[key], key[0], key[1]),
    )

    if start_date == end_date:
        name = (
            f"Order {start_date.day:02d} "
            f"{MONTH_NAMES[start_date.month]} {start_date.year}"
        )
    elif (
        start_date.year == end_date.year
        and start_date.month == end_date.month
    ):
        name = (
            f"Order {start_date.day:02d}-{end_date.day:02d} "
            f"{MONTH_NAMES[start_date.month]} {start_date.year}"
        )
    elif start_date.year == end_date.year:
        name = (
            f"Order {MONTH_NAMES[start_date.month]}-"
            f"{MONTH_NAMES[end_date.month]} {start_date.year}"
        )
    else:
        name = f"Order {start_date.year}-{end_date.year}"

    return {
        "name": name,
        "start_date": start_date,
        "end_date": end_date,
        "dominant_month": dominant_month,
        "dominant_year": dominant_year,
    }


def refresh_active_session_auto_name() -> Dict[str, object]:
    active = get_active_extraction_session()
    if not active or active.get("name_source") == "manual":
        return active

    from db.persistence import load_all_order_rows

    rows = load_all_order_rows()
    inferred = build_automatic_session_name(
        str(row.get("tgl_ro", "") or "") for row in rows
    )
    if not inferred:
        touch_active_extraction_session()
        return get_active_extraction_session()

    session_id = uuid.UUID(str(active["id"]))
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE public.extraction_sessions
                SET name = :name,
                    inferred_start_date = :start_date,
                    inferred_end_date = :end_date,
                    dominant_month = :dominant_month,
                    dominant_year = :dominant_year,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :session_id
                  AND name_source = 'auto'
                """
            ),
            {
                "session_id": session_id,
                **inferred,
            },
        )
    return get_active_extraction_session()


def export_active_session_bundle() -> bytes:
    active = get_active_extraction_session()
    if not active:
        return b""

    from db.persistence import (
        load_all_order_rows,
        load_all_raw_chat_records,
        load_stage2_match_audits,
    )

    orders = load_all_order_rows()
    raw_chats = load_all_raw_chat_records()
    audits = load_stage2_match_audits(100000)
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", str(active.get("name", "session"))).strip("_")
    safe_name = safe_name or "session"

    order_columns = [
        "job_number",
        "tgl_ro",
        "tgl_muat",
        "pickup",
        "tujuan",
        "no_plat",
        "type_truck",
        "driver",
        "kontak_driver",
        "status_unit",
    ]
    order_df = pd.DataFrame(orders)
    for column in order_columns:
        if column not in order_df.columns:
            order_df[column] = ""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            f"{safe_name}/session.json",
            json.dumps(active, ensure_ascii=False, indent=2, default=str),
        )
        archive.writestr(
            f"{safe_name}/orders.csv",
            order_df[order_columns].to_csv(index=False),
        )
        archive.writestr(
            f"{safe_name}/raw_chats.json",
            json.dumps(raw_chats, ensure_ascii=False, indent=2, default=str),
        )
        archive.writestr(
            f"{safe_name}/stage2_audits.json",
            json.dumps(audits, ensure_ascii=False, indent=2, default=str),
        )
        archive.writestr(
            f"{safe_name}/manifest.json",
            json.dumps(
                {
                    "exported_at": datetime.now().isoformat(timespec="seconds"),
                    "database": TEST_DATABASE_NAME,
                    "session_id": active.get("id"),
                    "row_count": len(orders),
                    "chat_count": len(raw_chats),
                    "audit_count": len(audits),
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
    return buffer.getvalue()
