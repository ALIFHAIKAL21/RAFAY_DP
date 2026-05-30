from __future__ import annotations

import html

import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
from sqlalchemy import text
# pyrefly: ignore [missing-import]
from sqlalchemy.engine import Connection, Engine


_NULL_LIKE = {"", "-", "none", "null", "nan", "undefined", "nat"}
_BATCH_LIMIT_OPTIONS = [10, 25, 50, 100, "Semua"]
_WA_SPLIT_PATTERN = r"(?=\[\d{2}[.,:]\d{2}[, ]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*[^:]+:)"
_REQUEST_HEADER_PATTERN = (
    r"(?im)^\s*"
    r"(?:\[\d{1,2}[.,:]\d{2}[, ]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*[^:]+:\s*)?"
    r"(?:request|req)\s+(?:ulang\s+)?(?:order|unit)\b"
)

_SQL_BATCH_UPLOADS = """
SELECT
    CAST(rc.id AS TEXT) AS raw_chat_id,
    rc.chat_hash,
    rc.chat_text,
    rc.created_at AS chat_created_at,
    COUNT(od.id) AS output_rows,
    SUM(CASE WHEN UPPER(COALESCE(od.status_unit, '')) = 'ASSIGNED' THEN 1 ELSE 0 END) AS assigned_rows,
    SUM(CASE WHEN UPPER(COALESCE(od.status_unit, '')) = 'PARTIAL' THEN 1 ELSE 0 END) AS partial_rows
FROM raw_chats rc
LEFT JOIN order_dataset od
    ON od.raw_chat_id = rc.id
GROUP BY rc.id, rc.chat_hash, rc.chat_text, rc.created_at
ORDER BY rc.created_at DESC
LIMIT :batch_limit
"""

_SQL_BATCH_UPLOADS_ALL = """
SELECT
    CAST(rc.id AS TEXT) AS raw_chat_id,
    rc.chat_hash,
    rc.chat_text,
    rc.created_at AS chat_created_at,
    COUNT(od.id) AS output_rows,
    SUM(CASE WHEN UPPER(COALESCE(od.status_unit, '')) = 'ASSIGNED' THEN 1 ELSE 0 END) AS assigned_rows,
    SUM(CASE WHEN UPPER(COALESCE(od.status_unit, '')) = 'PARTIAL' THEN 1 ELSE 0 END) AS partial_rows
FROM raw_chats rc
LEFT JOIN order_dataset od
    ON od.raw_chat_id = rc.id
GROUP BY rc.id, rc.chat_hash, rc.chat_text, rc.created_at
ORDER BY rc.created_at DESC
"""

_SQL_BATCH_ROWS = """
SELECT
    CAST(od.id AS TEXT) AS order_row_id,
    CAST(od.raw_chat_id AS TEXT) AS raw_chat_id,
    od.job_number,
    od.tgl_ro,
    od.tgl_muat,
    od.pickup,
    od.tujuan,
    od.type_truck,
    od.driver,
    od.no_plat,
    od.kontak_driver,
    od.status_unit,
    od.created_at AS order_created_at
FROM order_dataset od
WHERE CAST(od.raw_chat_id AS TEXT) = :raw_chat_id
ORDER BY od.created_at ASC, od.id ASC
"""

_OUTPUT_COLUMNS = [
    "job_number",
    "tgl_ro",
    "tgl_muat",
    "pickup",
    "tujuan",
    "type_truck",
    "driver",
    "no_plat",
    "kontak_driver",
    "status_unit",
]

_OUTPUT_LABELS = {
    "job_number": "Job Number",
    "tgl_ro": "Tgl RO",
    "tgl_muat": "Tgl Muat",
    "pickup": "Pickup",
    "tujuan": "Tujuan",
    "type_truck": "Type Truck",
    "driver": "Driver",
    "no_plat": "No. Plat",
    "kontak_driver": "Kontak Driver",
    "status_unit": "Status Unit",
}


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ui-bg: #ffffff;
            --ui-surface: #ffffff;
            --ui-surface-muted: #f9fafb;
            --ui-border: #d1d5db;
            --ui-border-strong: #9ca3af;
            --ui-text: #111827;
            --ui-text-muted: #4b5563;
            --ui-text-soft: #6b7280;
        }
        .stApp {
            background: var(--ui-bg) !important;
            color: var(--ui-text) !important;
        }
        header[data-testid="stHeader"] {
            visibility: visible !important;
        }
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            visibility: visible !important;
            display: flex !important;
            opacity: 1 !important;
        }
        .stMarkdown, .stCaption, .stMetric, p, span, label, h1, h2, h3, h4 {
            color: var(--ui-text) !important;
        }
        [data-testid="stDataFrame"] tbody td {
            color: var(--ui-text) !important;
            background: var(--ui-surface) !important;
            border-color: #e5e7eb !important;
            font-size: 0.77rem !important;
        }
        [data-testid="stDataFrame"] thead th {
            color: var(--ui-text-muted) !important;
            background: var(--ui-surface-muted) !important;
            border-color: #e5e7eb !important;
            font-size: 0.68rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.04em !important;
        }
        div.stButton > button {
            background: var(--ui-surface) !important;
            color: var(--ui-text) !important;
            border: 1px solid var(--ui-border-strong) !important;
            border-radius: 0.45rem !important;
            font-weight: 700 !important;
            box-shadow: none !important;
            min-height: 2.1rem !important;
        }
        div.stButton > button:hover {
            background: #f4f4f5 !important;
            color: var(--ui-text) !important;
        }
        .batch-title {
            padding: 0.62rem 0.88rem;
            border-radius: 0.55rem;
            border: 1px solid var(--ui-border);
            background: var(--ui-surface);
            color: var(--ui-text);
            font-weight: 700;
            margin-bottom: 0.35rem;
            letter-spacing: 0.01em;
        }
        .batch-subtitle {
            color: var(--ui-text-soft);
            font-size: 0.76rem;
            margin-bottom: 0.55rem;
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.45rem;
            margin: 0.15rem 0 0.62rem;
        }
        .kpi-card {
            border: 1px solid var(--ui-border);
            border-radius: 0.5rem;
            background: var(--ui-surface);
            padding: 0.5rem 0.6rem;
        }
        .kpi-label {
            font-size: 0.64rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--ui-text-soft);
            margin-bottom: 0.16rem;
            font-weight: 700;
        }
        .kpi-value {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.92rem;
            color: var(--ui-text);
            font-weight: 800;
        }
        .batch-headline {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            margin-bottom: 0.45rem;
        }
        .mini-chip {
            border: 1px solid var(--ui-border);
            border-radius: 999px;
            padding: 0.18rem 0.52rem;
            font-size: 0.69rem;
            color: var(--ui-text-muted);
            background: var(--ui-surface-muted);
            line-height: 1.2;
            font-weight: 600;
        }
        .ml-problem-badge {
            display: inline-flex;
            align-items: center;
            margin-left: 0.35rem;
            padding: 0.08rem 0.36rem;
            border-radius: 999px;
            border: 1px solid #fecaca;
            background: #fef2f2;
            color: #991b1b;
            font-size: 0.58rem;
            font-weight: 800;
            line-height: 1.1;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            white-space: nowrap;
        }
        div[data-baseweb="tab-list"] {
            gap: 0.3rem;
        }
        div[data-baseweb="tab-list"] button {
            padding: 0.24rem 0.6rem !important;
            border-radius: 0.38rem !important;
            border: 1px solid var(--ui-border) !important;
            background: var(--ui-surface) !important;
            font-size: 0.72rem !important;
            color: var(--ui-text-muted) !important;
            min-height: 1.9rem !important;
        }
        div[data-baseweb="tab-list"] button[aria-selected="true"] {
            border-color: var(--ui-border-strong) !important;
            color: var(--ui-text) !important;
            font-weight: 700 !important;
            background: var(--ui-surface-muted) !important;
        }
        div[data-testid="stExpander"] {
            border: 1px solid var(--ui-border);
            border-radius: 0.55rem;
            background: var(--ui-surface);
        }
        div[data-testid="stExpander"] details summary p {
            font-size: 0.76rem !important;
            font-weight: 700 !important;
            color: var(--ui-text) !important;
        }
        .block-title {
            margin-top: 0.1rem;
            margin-bottom: 0.35rem;
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            color: var(--ui-text-muted);
            text-transform: uppercase;
        }
        .ml-audit-card {
            margin-top: 0.4rem;
            border: 1px solid var(--ui-border);
            border-radius: 0.5rem;
            background: var(--ui-surface-muted);
            overflow: hidden;
            box-shadow: none;
        }
        .ml-audit-card details {
            margin: 0;
        }
        .ml-audit-card summary {
            list-style: none;
            cursor: pointer;
        }
        .ml-audit-card summary::-webkit-details-marker {
            display: none;
        }
        .ml-audit-card summary::marker {
            content: "";
        }
        .ml-audit-summary {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.6rem;
            padding: 0.48rem 0.62rem;
            border-bottom: 1px solid transparent;
            color: var(--ui-text);
        }
        .ml-audit-card details[open] .ml-audit-summary {
            border-bottom-color: var(--ui-border);
        }
        .ml-audit-title {
            font-size: 0.67rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            color: var(--ui-text-muted);
            white-space: nowrap;
        }
        .ml-audit-pills {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 0.35rem;
            flex: 1;
        }
        .ml-score-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 0.28rem;
            padding: 0.18rem 0.45rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.66rem;
            font-weight: 700;
            border: 1px solid var(--ui-border);
            color: var(--ui-text-muted) !important;
            background: var(--ui-surface) !important;
            white-space: nowrap;
        }
        .ml-score-good {
            color: #166534 !important;
            background: #f0fdf4 !important;
            border-color: #bbf7d0 !important;
        }
        .ml-score-warn {
            color: #854d0e !important;
            background: #fefce8 !important;
            border-color: #fde68a !important;
        }
        .ml-score-bad {
            color: #991b1b !important;
            background: #fef2f2 !important;
            border-color: #fecaca !important;
        }
        .ml-audit-toggle {
            font-size: 0.66rem;
            font-weight: 700;
            color: var(--ui-text-soft);
            white-space: nowrap;
        }
        .ml-audit-card details[open] .ml-toggle-closed,
        .ml-audit-card details:not([open]) .ml-toggle-open {
            display: none;
        }
        .ml-audit-body {
            padding: 0.52rem 0.62rem 0.62rem;
            display: grid;
            grid-template-columns: minmax(0, 1fr);
            gap: 0.52rem;
        }
        .ml-metric-section {
            border: 1px solid var(--ui-border);
            border-radius: 0.375rem;
            background: var(--ui-surface);
            padding: 0.54rem;
        }
        .ml-section-title {
            font-size: 0.66rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            color: var(--ui-text);
            text-transform: uppercase;
            margin-bottom: 0.34rem;
        }
        .ml-section-subtitle {
            color: var(--ui-text-soft);
            font-weight: 600;
            letter-spacing: 0;
            text-transform: none;
        }
        .ml-stat-line {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.72rem;
            color: var(--ui-text);
            background: var(--ui-surface-muted);
            border: 1px solid var(--ui-border);
            border-radius: 0.375rem;
            padding: 0.36rem 0.46rem;
            margin-bottom: 0.38rem;
            line-height: 1.55;
        }
        .ml-stat-line strong {
            color: var(--ui-text);
        }
        .ml-batch-summary-card .ml-audit-summary {
            padding: 0.58rem 0.72rem;
        }
        .ml-batch-summary-card .ml-audit-title {
            font-size: 0.78rem;
            font-weight: 800;
            color: var(--ui-text);
        }
        .ml-batch-summary-card .ml-score-pill {
            font-size: 0.73rem;
            font-weight: 800;
            padding: 0.22rem 0.52rem;
        }
        .ml-batch-summary-card .ml-stat-line {
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.42rem 0.52rem;
            line-height: 1.44;
        }
        .ml-batch-summary-card .ml-stat-line strong {
            font-weight: 900;
        }
        .ml-batch-summary-card .ml-batch-slot-section {
            padding: 0.58rem;
        }
        .ml-batch-summary-card .ml-batch-slot-section .ml-section-title {
            font-size: 0.78rem;
            font-weight: 900;
            color: var(--ui-text);
            margin-bottom: 0.4rem;
        }
        .ml-batch-summary-card .ml-batch-slot-section .ml-section-subtitle {
            font-weight: 800;
            color: var(--ui-text-muted);
        }
        .ml-batch-summary-card .ml-slot-table {
            font-size: 0.76rem;
            line-height: 1.42;
        }
        .ml-batch-summary-card .ml-slot-table th {
            font-size: 0.71rem;
            font-weight: 800;
            color: var(--ui-text);
            padding: 0.37rem 0.5rem;
        }
        .ml-batch-summary-card .ml-slot-table td {
            font-size: 0.76rem;
            padding: 0.3rem 0.5rem;
        }
        .ml-batch-summary-card .ml-slot-table td.num {
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.01em;
        }
        .ml-batch-summary-card .ml-slot-table td.field-name {
            font-size: 0.78rem;
            font-weight: 800;
            color: var(--ui-text);
        }
        .ml-batch-summary-card .ml-slot-table tr.row-total td {
            font-weight: 900;
            background: #eef0f2;
        }
        .ml-batch-summary-card .ml-slot-table tr.row-total td.num {
            font-size: 0.86rem;
            font-weight: 900;
        }
        .ml-batch-summary-card .ml-slot-f1-good,
        .ml-batch-summary-card .ml-slot-f1-warn,
        .ml-batch-summary-card .ml-slot-f1-bad {
            font-weight: 800;
        }
        .ml-metric-title {
            font-size: 1.02rem;
            font-weight: 900;
            letter-spacing: 0.02em;
            line-height: 1.08;
            color: var(--ui-text);
            margin-bottom: 0.42rem;
        }
        .ml-metric-subtitle {
            font-size: 0.78rem;
            font-weight: 900;
            letter-spacing: 0.01em;
            color: var(--ui-text);
            margin-left: 0.3rem;
        }
        .ml-metric-stat-line {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 1.03rem;
            font-weight: 900;
            color: var(--ui-text);
            background: var(--ui-surface-muted);
            border: 1px solid var(--ui-border);
            border-radius: 0.5rem;
            padding: 0.5rem 0.65rem;
            margin-bottom: 0.38rem;
            line-height: 1.32;
            letter-spacing: 0.01em;
        }
        .ml-metric-stat-line strong {
            color: var(--ui-text);
            font-weight: 900;
        }
        .ml-log-title {
            font-size: 0.64rem;
            font-weight: 700;
            color: var(--ui-text-soft);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 0.08rem 0 0.28rem;
        }
        .ml-log-row {
            border-left: 3px solid var(--ui-border-strong);
            background: #fafafa;
            padding: 0.35rem 0.5rem;
            margin-top: 0.28rem;
            border-radius: 0 0.25rem 0.25rem 0;
            color: var(--ui-text);
            font-size: 0.74rem;
            line-height: 1.5;
        }
        .ml-log-row b { color: var(--ui-text); }
        .ml-log-fp {
            border-left-color: #ef4444;
            background: #fef2f2;
        }
        .ml-log-fn {
            border-left-color: #f59e0b;
            background: #fffbeb;
        }
        .ml-log-ok {
            border-left-color: #22c55e;
            background: #f0fdf4;
        }
        .ml-analysis {
            border-left: 3px solid #3b82f6;
            background: #eff6ff;
            padding: 0.35rem 0.5rem;
            margin-top: 0.28rem;
            border-radius: 0 0.25rem 0.25rem 0;
            color: var(--ui-text);
            font-size: 0.74rem;
            line-height: 1.5;
        }
        .ml-tag {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.66rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            color: var(--ui-text) !important;
        }
        .ml-log-sub {
            display: block;
            padding-left: 0.75rem;
            margin-top: 0.15rem;
            font-size: 0.72rem;
            line-height: 1.45;
        }
        @media (max-width: 1080px) {
            .kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 900px) {
            .ml-audit-summary {
                align-items: flex-start;
                flex-direction: column;
            }
            .ml-audit-pills {
                justify-content: flex-start;
            }
        }
        .ml-slot-wrap {
            overflow-x: auto;
            margin-top: 0.12rem;
        }
        .ml-slot-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.7rem;
            line-height: 1.35;
        }
        .ml-slot-table th {
            background: var(--ui-surface-muted);
            color: var(--ui-text-soft);
            font-size: 0.63rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.32rem 0.46rem;
            border-bottom: 1px solid var(--ui-border);
            text-align: left;
            white-space: nowrap;
        }
        .ml-slot-table th.num {
            text-align: right;
        }
        .ml-slot-table td {
            padding: 0.27rem 0.46rem;
            border-bottom: 1px solid #eceef0;
            color: var(--ui-text);
            white-space: nowrap;
        }
        .ml-slot-table td.num {
            text-align: right;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.68rem;
        }
        .ml-slot-table td.field-name {
            font-weight: 600;
            color: var(--ui-text-muted);
        }
        .ml-slot-table tr:hover td {
            background: var(--ui-surface-muted);
        }
        .ml-slot-table tr.row-total td {
            background: #f1f2f3;
            font-weight: 700;
            border-top: 1px solid var(--ui-border-strong);
            border-bottom: none;
            color: var(--ui-text);
        }
        .ml-slot-f1-good {
            color: #166534 !important;
            font-weight: 700;
        }
        .ml-slot-f1-warn {
            color: #b45309 !important;
            font-weight: 700;
        }
        .ml-slot-f1-bad {
            color: #dc2626 !important;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    return _to_text(value).lower() in _NULL_LIKE


def _named_to_pyformat(sql: str) -> str:
    return re.sub(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)", r"%(\1)s", sql)


def _read_sql(engine_or_conn: Any, sql: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    params = params or {}
    if isinstance(engine_or_conn, Engine):
        with engine_or_conn.connect() as conn:
            return pd.read_sql_query(text(sql), conn, params=params)

    if isinstance(engine_or_conn, Connection):
        return pd.read_sql_query(text(sql), engine_or_conn, params=params)

    if hasattr(engine_or_conn, "cursor"):
        dbapi_sql = _named_to_pyformat(sql)
        return pd.read_sql_query(dbapi_sql, engine_or_conn, params=params)

    raise TypeError("engine_or_conn harus SQLAlchemy Engine/Connection atau DB-API connection.")


def _format_timestamp(value: Any) -> str:
    if value is None:
        return "-"
    try:
        ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return "-"
        return ts.strftime("%d %b %Y %H:%M:%S")
    except Exception:
        return _to_text(value) or "-"


def _normalize_compact(value: Any) -> str:
    if _is_blank(value):
        return ""
    raw = _to_text(value).upper()
    return re.sub(r"[^A-Z0-9]+", "", raw)


def _normalize_name(value: Any) -> str:
    if _is_blank(value):
        return ""
    raw = _to_text(value).upper()
    raw = re.sub(r"[^A-Z0-9 ]+", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()


def _normalize_phone(value: Any) -> str:
    if _is_blank(value):
        return ""
    digits = re.sub(r"\D+", "", _to_text(value))
    if digits.startswith("62"):
        digits = "0" + digits[2:]
    elif digits.startswith("8"):
        digits = "0" + digits
    return digits


# ---------------------------------------------------------------------------
# ATURAN 1 — Spill-over label detection for the EVALUATOR
# ---------------------------------------------------------------------------
# When the raw input text has an empty driver field like:
#     driver  :
#     Nopol  : B 9563 TEU
# A naive regex may capture "Nopol" or "Nopol :" as the driver name.
# This function detects such spill-over values so the evaluator can
# treat the driver as genuinely empty (→ PARTIAL status is correct).
_KNOWN_LABEL_KEYWORDS = {
    "nopol", "no pol", "no plat", "plat", "no polisi",
    "no hp", "no tlp", "no telp", "no telepon", "kontak", "hp",
    "tlp", "telp", "phone",
    "lokasi", "rute", "tujuan", "rute/tujuan",
    "waktu loading", "type truck", "jenis unit", "unit",
    "driver", "nama driver", "nama",
}


def _is_spilled_label(value: str) -> bool:
    """Return True if `value` looks like a label keyword (spill-over artifact).

    Examples that return True:
        'Nopol :', 'Nopol', 'No hp  :', 'no Hp', ' : ', ''
    Examples that return False:
        'SUTRISNO', 'B 9563 TEU', '0812345678'
    """
    cleaned = re.sub(r'[:\s]+', ' ', value).strip().lower()
    if not cleaned:
        return True
    # Check if the cleaned value matches any known label keyword
    if cleaned in _KNOWN_LABEL_KEYWORDS:
        return True
    # Also check if it starts with a label keyword followed by optional colon
    for kw in _KNOWN_LABEL_KEYWORDS:
        if cleaned == kw or cleaned.startswith(kw + ' '):
            return True
    return False


def _sanitize_driver_value(raw_driver: str) -> str:
    """Sanitize a raw driver value: return empty string if it's a spill-over label.

    This is the EVALUATOR-side guard against BUG 1.  Even if the regex
    accidentally captures 'Nopol :' as the driver, this function strips it.
    """
    if _is_spilled_label(raw_driver):
        return ""
    return raw_driver.strip()


# ---------------------------------------------------------------------------
# GROUND TRUTH EXTRACTOR
# ---------------------------------------------------------------------------
# Boundary pattern: stop extracting a field value when we hit a newline
# or the start of the next known label.  This prevents BUG 1 (spill-over).
_GT_FIELD_BOUNDARY = (
    r"(?=\s*$"               # end-of-line (possibly trailing spaces)
    r"|(?:\r?\n)"            # or literal newline
    r"|(?:(?:driver|nama\s*driver|nopol|no\.?\s*pol|no\.?\s*plat|plat"
    r"|no\.?\s*hp|no\.?\s*tlp|no\.?\s*telp|kontak|hp|tlp|phone"
    r"|lokasi|rute|waktu\s*loading|type\s*truck|jenis\s*unit|unit)\s*:))"
)

# Indonesian month lookup (case-insensitive).
# Includes common typos found in real WhatsApp logistics chats
# (e.g. "FEBUARI", "febuary", "agutus", "novmber", etc.).
_BULAN_MAP = {
    # ── Canonical Indonesian names ──
    "januari": "01", "februari": "02", "maret": "03", "april": "04",
    "mei": "05", "juni": "06", "juli": "07", "agustus": "08",
    "september": "09", "oktober": "10", "november": "11", "desember": "12",
    # ── Standard abbreviations ──
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    # ── English full names (sometimes used in ID chats) ──
    "january": "01", "february": "02", "march": "03",
    "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    # ── Common typos observed in real data ──
    "febuari": "02",    # swapped 'r' and 'u' — very frequent
    "febuary": "02",    # English-style typo
    "pebruari": "02",   # 'p' instead of 'f'
    "agutus": "08",     # missing 's'
    "agsts": "08",      # SMS-style abbreviation
    "novmber": "11",    # missing 'e'
    "desembar": "12",   # 'a' instead of 'e'
    "nopember": "11",   # 'p' instead of 'v'
}


def _parse_indonesian_date(text: str) -> str:
    """Parse free-form Indonesian date string into 'DD BULAN YYYY' format.

    Handles patterns like:
      '13 FEBRUARI 2026', '12 Feb 26', '13/03/2026', '14-02-2026',
      '13-03-26', '06 FEB 2026'
    Returns empty string if unparseable.
    """
    text = text.strip()
    if not text:
        return ""

    # Pattern 1: "13 FEBRUARI 2026" or "06 FEB 2026" (Indonesian named month)
    m = re.search(
        r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{2,4})",
        text,
    )
    if m:
        day = m.group(1).zfill(2)
        month_str = m.group(2).lower()
        year = m.group(3)
        if len(year) == 2:
            year = "20" + year
        month_num = _BULAN_MAP.get(month_str)
        if month_num:
            # Reverse-lookup full month name for consistent output
            full_months = [
                "JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI",
                "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER",
            ]
            month_name = full_months[int(month_num) - 1]
            return f"{day} {month_name} {year}"

    # Pattern 2: "13/03/2026", "14-02-2026", "13-03-26"  (DD/MM/YYYY or DD-MM-YY)
    # Use findall + validation: inputs like "06:00/13-03-26" yield two matches,
    # the first (00/13/03) is invalid, the second (13/03/26) is correct.
    for m in re.finditer(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})", text):
        day_str = m.group(1)
        month_str = m.group(2)
        year = m.group(3)
        day_int = int(day_str)
        month_int = int(month_str)
        # Validate: day must be 1-31, month must be 1-12
        if day_int < 1 or day_int > 31 or month_int < 1 or month_int > 12:
            continue
        day = day_str.zfill(2)
        if len(year) == 2:
            year = "20" + year
        full_months = [
            "JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI",
            "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER",
        ]
        return f"{day} {full_months[month_int - 1]} {year}"

    return ""


def _extract_tgl_ro_from_header(header_text: str) -> str:
    """Extract 'Tanggal RO' from the WA chat header line.

    Looks for patterns like:
      'REQUEST ORDER ONCALL 13 FEBRUARI 2026'
      'Request Unit On Call Tgl 12 MARET 2026'
      'REQUEST ORDER ULANG ONCALL\\n06 FEB 2026'
      'Request Unit On Call Tgl 12 Feb 26'

    IMPORTANT: The header line contains BOTH a WhatsApp timestamp
    (e.g. "[05.31, 7/3/2026]") AND the actual RO date. We must extract
    the RO date, NOT the WA timestamp. Strategy:
      1. Strip the WA timestamp prefix from the header.
      2. Then parse the remaining text for the RO date.
    """
    lines = header_text.strip().split("\n")
    search_text = " ".join(lines[:3])  # combine first 3 lines for multi-line headers

    # Strip the WA timestamp prefix to avoid confusing "7/3/2026" with the RO date.
    # WA format: "[HH.MM, D/M/YYYY] SenderName: ..."
    wa_timestamp_match = re.match(
        r"^\s*\[(\d{2}[.,:]?\d{2})[, ]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\]\s*[^:]*:\s*",
        search_text,
    )
    cleaned_text = re.sub(
        r"^\s*\[\d{2}[.,:]?\d{2}[, ]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*[^:]*:\s*",
        "",
        search_text,
    )

    # Primary: parse the RO date from the cleaned header text
    result = _parse_indonesian_date(cleaned_text)
    if result:
        return result

    # Fallback: if no explicit RO date in header text (e.g. "REQUEST ORDER ULANG ONCALL"
    # with no date), fall back to the WA message timestamp date.
    if wa_timestamp_match:
        return _parse_indonesian_date(wa_timestamp_match.group(2))

    return ""


def _extract_tgl_muat(waktu_loading_value: str, tgl_ro: str) -> str:
    """Determine 'Tanggal Muat' based on 3 business conditions.

    KONDISI A: Only time (e.g. '15:00')       → tgl_muat = tgl_ro
    KONDISI B: Time + date (e.g. '15:00 / 14 febuari 2026') → parse the date
    KONDISI C: Keyword 'segera'               → tgl_muat = tgl_ro
    """
    raw = waktu_loading_value.strip()
    if not raw:
        return tgl_ro

    # KONDISI C: "segera" (case-insensitive)
    if re.match(r"(?i)^\s*segera\s*$", raw):
        return tgl_ro

    # Try to parse an explicit date from the waktu loading field.
    # First, strip any leading time portion (e.g. "06:00/", "15:00 ", "02:00 ")
    # so the date parser sees a clean date string.
    date_portion = re.sub(r"^\d{1,2}[:.]\d{2}\s*[/\s]*", "", raw).strip()

    # Try the cleaned date portion first
    if date_portion:
        parsed_date = _parse_indonesian_date(date_portion)
        if parsed_date:
            return parsed_date

    # Also try the full raw string (handles "14 febuari 2026" without time prefix)
    parsed_date = _parse_indonesian_date(raw)
    if parsed_date:
        return parsed_date

    # KONDISI A: Only time pattern (HH:MM or HH.MM), no date found
    if re.search(r"\d{1,2}[:.]\d{2}", raw):
        return tgl_ro

    # Fallback: cannot determine, use tgl_ro
    return tgl_ro


def _safe_field_value(pattern: str, text: str) -> str:
    """Extract a field value using regex, stopping at line boundary.

    This prevents BUG 1 (spill-over) where an empty field like:
        driver  :
        Nopol  : B 9563 TEU
    would incorrectly capture 'Nopol  : B 9563 TEU' as the driver name.

    All caller patterns MUST use [^\\r\\n]* to constrain capture to a single line.
    """
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if not match:
        return ""
    val = match.group(1).strip()
    if not val:
        return ""
    return val


def extract_ground_truth_entities(raw_text: str) -> List[Dict[str, Any]]:
    """Extract ground truth entities from raw WhatsApp chat text.

    Returns a list of dicts, one per truck/unit, each with keys:
        tgl_ro, tgl_muat, pickup, tujuan, type_truck,
        driver, nopol, no_hp, status_unit

    Compatible with calculate_batch_micro_metrics() pipeline.
    """
    results: List[Dict[str, Any]] = []

    # ── Step 1: Extract global Tanggal RO from the header ──
    tgl_ro = _extract_tgl_ro_from_header(raw_text)

    # ── Step 2: Extract shared fields from the header block ──
    # Pickup (Lokasi) — shared across all units in this chat block
    pickup = _safe_field_value(
        r"^\s*lokasi\s*:[ \t]*([^\r\n]*)",
        raw_text,
    )

    # Type Truck — from the "N UNIT TYPE SIZE CBM" line
    type_truck = ""
    m_unit = re.search(
        r"(?im)^\s*\d{1,3}\s*unit\s+([A-Za-z][A-Za-z0-9/]*)",
        raw_text,
    )
    if m_unit:
        type_truck = m_unit.group(1).strip().upper()

    # ── Step 3: Split into per-unit sections ──
    # Each unit section starts with "Waktu loading" (the primary delimiter).
    # We split the text at each "Waktu loading" occurrence.
    unit_sections = re.split(
        r"(?i)(?=(?:^|\n)\s*waktu\s*loading\s*:)",
        raw_text,
    )

    for section in unit_sections:
        section = section.strip()
        if not section:
            continue

        # Only process sections that actually contain "Waktu loading"
        wl_match = re.search(
            r"(?i)waktu\s*loading\s*:\s*([^\n]*)",
            section,
        )
        if not wl_match:
            continue

        waktu_loading_raw = wl_match.group(1).strip()

        # ── Step 4: Apply Tanggal Muat logic (fixes BUG 2) ──
        tgl_muat = _extract_tgl_muat(waktu_loading_raw, tgl_ro)

        # ── Step 5: Extract per-unit fields with safe boundary (fixes BUG 1) ──
        # All patterns use ^...([^\r\n]*) with re.MULTILINE.
        # [^\r\n]* is an absolute barrier — it CANNOT cross a line boundary.

        tujuan = _safe_field_value(
            r"^\s*rute\s*/?\s*tujuan\s*:[ \t]*([^\r\n]*)",
            section,
        )

        # Driver regex:
        # - Matches "driver :", "driver 1 :", "driver2:", "Driver :",
        #   "nama driver :", "nama :"  (all case-insensitive)
        # - The optional \d* handles numbered drivers (e.g. "driver 1 :")
        # - [^\r\n]* constrains capture to the SAME line (prevents BUG 1)
        driver = _safe_field_value(
            r"^\s*(?:driver|nama(?:\s*driver)?)\s*\d*\s*:[ \t]*([^\r\n]*)",
            section,
        )

        nopol = _safe_field_value(
            r"^\s*(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)\s*:[ \t]*([^\r\n]*)",
            section,
        )

        # No HP regex:
        # - Matches "No hp", "No tlp", "No telp", "NO TLP", "kontak",
        #   "kontak driver", "hp", "phone"  (all case-insensitive)
        no_hp = _safe_field_value(
            r"^\s*(?:no\.?\s*(?:hp|tlp|telp|telepon)|kontak(?:\s*driver)?|hp|phone)\s*:[ \t]*([^\r\n]*)",
            section,
        )

        # Section-local pickup (some sections override the global one)
        local_pickup = _safe_field_value(
            r"^\s*lokasi\s*:[ \t]*([^\r\n]*)",
            section,
        )
        final_pickup = local_pickup if local_pickup else pickup

        # Section-local type_truck (rare but possible)
        local_unit = ""
        m_local_unit = re.search(
            r"(?im)^\s*\d{1,3}\s*unit\s+([A-Za-z][A-Za-z0-9/]*)",
            section,
        )
        if m_local_unit:
            local_unit = m_local_unit.group(1).strip().upper()
        final_type = local_unit if local_unit else type_truck

        # ── Step 6: Determine status_unit ──
        # ASSIGNED if driver is filled, PARTIAL otherwise
        status = "ASSIGNED" if driver else "PARTIAL"

        results.append({
            "tgl_ro": tgl_ro,
            "tgl_muat": tgl_muat,
            "pickup": final_pickup.upper() if final_pickup else "",
            "tujuan": tujuan.strip(),
            "type_truck": final_type,
            "driver": driver.strip(),
            "nopol": nopol.strip(),
            "no_hp": no_hp.strip(),
            "status_unit": status,
        })

    return results


def _normalize_route(value: Any) -> str:
    if _is_blank(value):
        return ""
    raw = _to_text(value).upper()
    raw = raw.replace("->", "-").replace("—", "-").replace("–", "-")
    raw = raw.replace("/", "-")
    parts = [
        _normalize_compact(p)
        for p in re.split(r"\s*-\s*|\s*,\s*", raw)
        if _normalize_compact(p)
    ]
    return ",".join(parts)


def _normalize_unit_type(value: Any) -> str:
    if _is_blank(value):
        return ""
    raw = _to_text(value).upper()
    raw = re.sub(r"[^A-Z0-9 ]+", " ", raw)
    tokens = [t for t in raw.split() if t]
    if not tokens:
        return ""
    return tokens[0]


def _split_wa_messages(chat_text: Any) -> List[str]:
    raw = str(chat_text or "")
    wa_messages = [m.strip() for m in re.split(_WA_SPLIT_PATTERN, raw) if m.strip()]
    if not wa_messages:
        wa_messages = [raw.strip()] if raw.strip() else []
    if not wa_messages:
        return []

    chat_blocks: List[str] = []
    for message in wa_messages:
        header_matches = list(re.finditer(_REQUEST_HEADER_PATTERN, message))
        if len(header_matches) <= 1:
            chat_blocks.append(message)
            continue

        for idx, match in enumerate(header_matches):
            start = match.start()
            end = header_matches[idx + 1].start() if idx + 1 < len(header_matches) else len(message)
            chunk = message[start:end].strip()
            if chunk:
                chat_blocks.append(chunk)

    return chat_blocks if chat_blocks else wa_messages


def _extract_qty(message_text: str) -> Optional[int]:
    m = re.search(r"(?i)\b(\d{1,3})\s*unit\b", message_text)
    if not m:
        return None
    try:
        qty = int(m.group(1))
        return qty if qty > 0 else None
    except Exception:
        return None


def _extract_line_value(pattern: str, text_value: str) -> str:
    match = re.search(pattern, text_value)
    return _to_text(match.group(1)) if match else ""


def _extract_unit_key(text_value: str) -> str:
    qty_line = _extract_line_value(r"(?im)^\s*\d{1,3}\s*unit\s+([A-Z][A-Z0-9]*)", text_value)
    if qty_line:
        return _normalize_unit_type(qty_line)

    type_line = _extract_line_value(
        r"(?im)^\s*(?:jenis\s+unit|type\s+truck|unit\s+type|type)\s*:\s*([^\n\r]+)",
        text_value,
    )
    if type_line:
        return _normalize_unit_type(type_line)

    unit_line = _extract_line_value(r"(?im)^\s*unit\s*:\s*([^\n\r]+)", text_value)
    if unit_line:
        return _normalize_unit_type(unit_line)

    return ""


def _extract_payload_fields(text_value: str) -> Dict[str, str]:
    pickup_raw = _extract_line_value(r"(?im)^\s*lokasi\s*:\s*([^\n\r]+)", text_value)
    route_raw = _extract_line_value(r"(?im)^\s*rute\s*/?\s*tujuan\s*:\s*([^\n\r]+)", text_value)
    # Driver regex: handles numbered drivers ("driver 1 :", "Driver2:") and
    # standalone "Nama :" label.  Must mirror the ground-truth extractor.
    driver_raw = _extract_line_value(
        r"(?im)^\s*(?:driver|nama(?:\s*driver)?)\s*\d*\s*:\s*([^\n\r]+)",
        text_value,
    )
    # ATURAN 1 — Sanitize: reject spill-over labels captured as driver name
    driver_raw = _sanitize_driver_value(driver_raw)

    plate_raw = _extract_line_value(
        r"(?im)^\s*(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)\s*:\s*([^\n\r]+)",
        text_value,
    )
    # Sanitize plate: reject spill-over labels (e.g. "No hp" captured as plate)
    if _is_spilled_label(plate_raw):
        plate_raw = ""

    phone_raw = _extract_line_value(
        r"(?im)^\s*(?:no\.?\s*(?:hp|tlp|telp|telepon)|kontak(?:\s*driver)?|hp|tlp|telp|phone)\s*:\s*([^\n\r]+)",
        text_value,
    )
    # Sanitize phone: reject spill-over labels
    if _is_spilled_label(phone_raw):
        phone_raw = ""

    return {
        "pickup_raw": pickup_raw,
        "route_raw": route_raw,
        "unit_raw": "",
        "driver_raw": driver_raw,
        "plate_raw": plate_raw,
        "phone_raw": phone_raw,
        "pickup_key": _normalize_compact(pickup_raw),
        "route_key": _normalize_route(route_raw),
        "unit_key": _extract_unit_key(text_value),
        "driver_key": _normalize_name(driver_raw),
        "plate_key": _normalize_compact(plate_raw),
        "phone_key": _normalize_phone(phone_raw),
    }


def _extract_block_payload(message_text: str) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "qty": _extract_qty(message_text),
        "pickup_key": "",
        "route_key": "",
        "unit_key": "",
        "driver_key": "",
        "plate_key": "",
        "phone_key": "",
    }

    payload.update({k: v for k, v in _extract_payload_fields(message_text).items() if k.endswith("_key")})
    return payload


def _display_route(route_key: Any) -> str:
    route_text = _to_text(route_key)
    if not route_text:
        return "-"
    return " - ".join([part for part in route_text.split(",") if part])


def _display_pct(value: float) -> str:
    """Display metric in decimal scale [0, 1] with 2 or 4 decimals."""
    try:
        metric = float(value)
    except Exception:
        metric = 0.0
    metric = max(0.0, min(1.0, metric))
    metric_4 = round(metric, 4)
    metric_2 = round(metric, 2)
    if abs(metric_4 - metric_2) < 1e-10:
        return f"{metric_2:.2f}"
    return f"{metric_4:.4f}"


def _metric_scores(tp: int, fp: int, fn: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def _classify_block_partition(message_text: str) -> Dict[str, str]:
    _ = message_text
    return {"domain": "new_order", "subtype": "new_order", "reason": "fallback_stage2_disabled"}


def calculate_batch_micro_metrics(
    batch_blocks_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute micro-averaged Precision / Recall / F1 at batch level.

    Micro-averaging aggregates the raw TP/FP/FN counts from **all** blocks
    into a single pool before calculating percentages.  This avoids the
    macro-averaging bias that occurs when block sizes are highly imbalanced
    (e.g. 1-truck vs. 10-truck orders).

    Parameters
    ----------
    batch_blocks_data : list[dict]
        Each dict represents one chat-block and must contain:
        - ``"record_metrics"``: ``{"tp": int, "fp": int, "fn": int}``
        - ``"slot_metrics"``:   ``{"tp": int, "fp": int, "fn": int}``
        An optional ``"block_id"`` key is carried through for traceability.

    Returns
    -------
    dict
        {
            "total_blocks": int,
            "record": {
                "tp": int, "fp": int, "fn": int,
                "precision": float, "recall": float, "f1": float
            },
            "slot": { ... same structure ... }
        }
        Precision / Recall / F1 are rounded to 4 decimal places (0-1 scale).
    """

    rec_tp = rec_fp = rec_fn = 0
    slot_tp = slot_fp = slot_fn = 0

    for block in batch_blocks_data:
        rm = block.get("record_metrics") or {}
        rec_tp += int(rm.get("tp") or 0)
        rec_fp += int(rm.get("fp") or 0)
        rec_fn += int(rm.get("fn") or 0)

        sm = block.get("slot_metrics") or {}
        slot_tp += int(sm.get("tp") or 0)
        slot_fp += int(sm.get("fp") or 0)
        slot_fn += int(sm.get("fn") or 0)

    rec_scores = _metric_scores(rec_tp, rec_fp, rec_fn)
    slot_scores = _metric_scores(slot_tp, slot_fp, slot_fn)

    return {
        "total_blocks": len(batch_blocks_data),
        "record": {
            "tp": rec_tp,
            "fp": rec_fp,
            "fn": rec_fn,
            "precision": round(rec_scores["precision"], 4),
            "recall": round(rec_scores["recall"], 4),
            "f1": round(rec_scores["f1"], 4),
        },
        "slot": {
            "tp": slot_tp,
            "fp": slot_fp,
            "fn": slot_fn,
            "precision": round(slot_scores["precision"], 4),
            "recall": round(slot_scores["recall"], 4),
            "f1": round(slot_scores["f1"], 4),
        },
    }


def _score_class(score: float) -> str:
    if score >= 0.8:
        return "ml-score-good"
    if score >= 0.5:
        return "ml-score-warn"
    return "ml-score-bad"


def _iter_assignment_sections(message_text: str) -> List[str]:
    sections: List[str] = []
    seen = set()
    chunks = re.split(r"(?im)(?=^\s*waktu\s+loading\s*:)", message_text)
    for chunk in chunks:
        for section in re.split(r"\n\s*\n", chunk):
            clean = section.strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            sections.append(clean)
    return sections


def _build_expected_slot(
    slot_id: str,
    status: str,
    base_fields: Dict[str, str],
    local_fields: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    local_fields = local_fields or {}
    slot: Dict[str, str] = {"slot_id": slot_id, "status": status}
    for name in ["pickup", "route", "unit"]:
        slot[f"{name}_raw"] = local_fields.get(f"{name}_raw") or base_fields.get(f"{name}_raw") or ""
        slot[f"{name}_key"] = local_fields.get(f"{name}_key") or base_fields.get(f"{name}_key") or ""
    for name in ["driver", "plate", "phone"]:
        slot[f"{name}_raw"] = local_fields.get(f"{name}_raw") or ""
        slot[f"{name}_key"] = local_fields.get(f"{name}_key") or ""
    return slot


def _extract_expected_slots(message_text: str, expected_rows: int) -> List[Dict[str, str]]:
    base_fields = _extract_payload_fields(message_text)
    assigned_slots: List[Dict[str, str]] = []

    for section in _iter_assignment_sections(message_text):
        fields = _extract_payload_fields(section)
        has_identity = bool(fields["driver_key"] or fields["plate_key"] or fields["phone_key"])
        if not has_identity:
            continue
        slot_id = f"P{len(assigned_slots) + 1}"
        assigned_slots.append(_build_expected_slot(slot_id, "ASSIGNED", base_fields, fields))

    if not assigned_slots and (base_fields["driver_key"] or base_fields["plate_key"] or base_fields["phone_key"]):
        assigned_slots.append(_build_expected_slot("P1", "ASSIGNED", base_fields, base_fields))

    assigned_slots = assigned_slots[:expected_rows]
    partial_count = max(0, expected_rows - len(assigned_slots))
    partial_slots = [
        _build_expected_slot(f"P{len(assigned_slots) + idx + 1}", "PARTIAL", base_fields)
        for idx in range(partial_count)
    ]
    return assigned_slots + partial_slots


def _row_has_identity(row: pd.Series) -> bool:
    return bool(row.get("driver_key") or row.get("plate_key") or row.get("phone_key"))


def _slot_has_identity(slot: Dict[str, str]) -> bool:
    return bool(slot.get("driver_key") or slot.get("plate_key") or slot.get("phone_key"))


def _row_duplicate_key(row: pd.Series) -> str:
    if _to_text(row.get("status_norm")).upper() == "PARTIAL":
        return ""
    if row.get("plate_key"):
        return f"plate:{row.get('plate_key')}"
    if row.get("phone_key"):
        return f"phone:{row.get('phone_key')}"
    if row.get("driver_key"):
        return "|".join(
            [
                "driver",
                _to_text(row.get("driver_key")),
                _to_text(row.get("pickup_key")),
                _to_text(row.get("route_key")),
            ]
        )
    return ""


def _detect_duplicate_rows(prepared: pd.DataFrame) -> set:
    groups: Dict[str, List[Any]] = {}
    for row_idx, row in prepared.iterrows():
        key = _row_duplicate_key(row)
        if not key:
            continue
        groups.setdefault(key, []).append(row_idx)

    duplicate_indices = set()
    for indices in groups.values():
        if len(indices) <= 1:
            continue
        ordered = sorted(indices, key=lambda idx: int(prepared.loc[idx, "_audit_row_no"]))
        duplicate_indices.update(ordered[1:])
    return duplicate_indices


def _score_expected_slot(slot: Dict[str, str], row: pd.Series) -> Tuple[int, int, int]:
    score = 0
    identity_hits = 0
    structure_hits = 0

    if slot.get("plate_key") and row.get("plate_key") and slot["plate_key"] == row["plate_key"]:
        score += 180
        identity_hits += 1
    if slot.get("phone_key") and row.get("phone_key") and slot["phone_key"] == row["phone_key"]:
        score += 150
        identity_hits += 1
    if slot.get("driver_key") and row.get("driver_key") and slot["driver_key"] == row["driver_key"]:
        score += 120
        identity_hits += 1

    if slot.get("pickup_key") and row.get("pickup_key") and slot["pickup_key"] == row["pickup_key"]:
        score += 45
        structure_hits += 1
    if slot.get("route_key") and row.get("route_key") and slot["route_key"] == row["route_key"]:
        score += 45
        structure_hits += 1
    if slot.get("unit_key") and row.get("unit_key") and slot["unit_key"] == row["unit_key"]:
        score += 30
        structure_hits += 1

    slot_status = _to_text(slot.get("status")).upper()
    row_status = _to_text(row.get("status_norm")).upper()
    if slot_status == "PARTIAL" and row_status == "PARTIAL":
        score += 90
        structure_hits += 1
    elif slot_status == "ASSIGNED" and row_status == "ASSIGNED":
        score += 20

    return score, identity_hits, structure_hits


# ---------------------------------------------------------------------------
# PER-FIELD SLOT EVALUATION WITH BUSINESS RULES (ATURAN 1 & 2)
# ---------------------------------------------------------------------------
def _compute_slot_field_metrics(
    pairs: List[Dict[str, Any]],
    unmatched_slots: List[Dict[str, str]],
    extra_indices: set,
    duplicate_indices: set,
    prepared: pd.DataFrame,
    message_text: str,
) -> Dict[str, Dict[str, int]]:
    """Compute per-field TP / FP / FN for every NER attribute.

    This function applies two critical business rules before scoring:

    ATURAN 1 — Driver & Status Unit validation:
        If the ground-truth driver value is a spill-over label (e.g. 'Nopol :'),
        the evaluator treats it as *empty*.  A model that outputs driver=''
        and status='PARTIAL' is therefore a True Positive, not an error.

    ATURAN 2 — Tanggal Muat validation hierarchy:
        The expected 'tgl_muat' is derived from 'Waktu loading' context:
          A) Time-only or 'SEGERA' → tgl_muat must equal tgl_ro
          B) Explicit date present  → tgl_muat must equal that date
        The evaluator uses extract_ground_truth_entities() output (which
        already implements these rules) as the canonical baseline, then
        applies tolerant matching against the model's prediction.

    Returns dict keyed by field name, each value = {tp, fp, fn}.
    """
    # ── Extract canonical ground truth from the raw message text ──
    gt_entities = extract_ground_truth_entities(message_text)

    def _expected_value_from_slot_or_gt(
        field_label: str,
        slot: Optional[Dict[str, str]],
        gt: Dict[str, Any],
    ) -> Optional[str]:
        """Return expected field value for evaluation.

        Priority:
          1) Slot-derived expectation (stable with pairing result)
          2) Ground-truth extractor fallback (for date fields / legacy support)

        Returns None for date fields when expectation is unavailable,
        so the evaluator can skip scoring that field instead of creating
        false FP/FN from parser gaps.
        """
        slot = slot or {}

        if field_label == "tgl_ro":
            val = _to_text(gt.get("tgl_ro", ""))
            return val or None
        if field_label == "tgl_muat":
            val = _to_text(gt.get("tgl_muat", ""))
            return val or None
        if field_label == "pickup":
            # Pickup is frequently inherited/global and parser coverage is less
            # reliable than identity fields. If expectation cannot be derived
            # from slot nor GT extractor, skip scoring this field to avoid
            # false-positive penalties in cumulative metrics.
            val = _to_text(slot.get("pickup_raw")) or _to_text(gt.get("pickup", ""))
            return val or None
        if field_label == "tujuan":
            return _to_text(slot.get("route_raw")) or _to_text(gt.get("tujuan", ""))
        if field_label == "type_truck":
            # unit_raw can be blank in some payload formats; use unit_key fallback.
            return (
                _to_text(slot.get("unit_raw"))
                or _to_text(slot.get("unit_key"))
                or _to_text(gt.get("type_truck", ""))
            )
        if field_label == "driver":
            return _to_text(slot.get("driver_raw")) or _to_text(gt.get("driver", ""))
        if field_label == "nopol":
            return _to_text(slot.get("plate_raw")) or _to_text(gt.get("nopol", ""))
        if field_label == "kontak_driver":
            return _to_text(slot.get("phone_raw")) or _to_text(gt.get("no_hp", ""))
        return _to_text(gt.get(field_label, ""))

    # Field definitions: (field_label, gt_key, model_column, normalizer)
    _EVAL_FIELD_DEFS = [
        ("tgl_ro",         "tgl_ro",      "tgl_ro",         _normalize_compact),
        ("tgl_muat",       "tgl_muat",    "tgl_muat",       _normalize_compact),
        ("pickup",         "pickup",      "pickup",         _normalize_compact),
        ("tujuan",         "tujuan",      "tujuan",         _normalize_route),
        ("type_truck",     "type_truck",  "type_truck",     _normalize_unit_type),
        ("driver",         "driver",      "driver",         _normalize_name),
        ("nopol",          "nopol",       "no_plat",        _normalize_compact),
        ("kontak_driver",  "no_hp",       "kontak_driver",  _normalize_phone),
    ]

    # Initialize counters
    field_metrics: Dict[str, Dict[str, int]] = {}
    for label, _, _, _ in _EVAL_FIELD_DEFS:
        field_metrics[label] = {"tp": 0, "fp": 0, "fn": 0}

    # ── Score matched pairs (slot↔row) ──
    for pair_idx, pair in enumerate(pairs):
        row = pair["row"]
        slot = pair.get("slot") or {}

        # Find the corresponding GT entity for this pair.
        # Use pair index if available; do not fallback to last entity because
        # that creates false penalties on PARTIAL / sparse blocks.
        gt = gt_entities[pair_idx] if pair_idx < len(gt_entities) else {}

        for field_label, gt_key, model_col, normalizer in _EVAL_FIELD_DEFS:
            gt_val_candidate = _expected_value_from_slot_or_gt(field_label, slot, gt)
            # Skip scoring unavailable date expectations (prevents false FP/FN).
            if gt_val_candidate is None:
                continue
            gt_val = _to_text(gt_val_candidate)
            pred_val = _to_text(row.get(model_col, ""))

            # ── ATURAN 1: Driver spill-over sanitization ──
            # If GT driver is a spill-over label, treat as empty.
            # Model outputting empty driver is then correct (TP).
            if field_label == "driver":
                gt_val = _sanitize_driver_value(gt_val)

            gt_norm = normalizer(gt_val)
            pred_norm = normalizer(pred_val)

            gt_empty = not gt_norm
            pred_empty = not pred_norm

            if gt_empty and pred_empty:
                # Both empty → TP (correct absence)
                field_metrics[field_label]["tp"] += 1
            elif gt_norm == pred_norm:
                # Exact match → TP
                field_metrics[field_label]["tp"] += 1
            else:
                # ── ATURAN 2: Tolerant tgl_muat matching ──
                # For tgl_muat, the GT has already been computed with the
                # correct Waktu Loading → Tanggal Muat hierarchy by
                # extract_ground_truth_entities().  But the model may output
                # the date in a slightly different format.  We apply tolerant
                # date comparison before declaring FP/FN.
                if field_label == "tgl_muat" and gt_norm and pred_norm:
                    gt_parsed = _parse_indonesian_date(gt_val)
                    pred_parsed = _parse_indonesian_date(pred_val)
                    if gt_parsed and pred_parsed and _normalize_compact(gt_parsed) == _normalize_compact(pred_parsed):
                        field_metrics[field_label]["tp"] += 1
                        continue

                # tgl_ro: same tolerant date comparison
                if field_label == "tgl_ro" and gt_norm and pred_norm:
                    gt_parsed = _parse_indonesian_date(gt_val)
                    pred_parsed = _parse_indonesian_date(pred_val)
                    if gt_parsed and pred_parsed and _normalize_compact(gt_parsed) == _normalize_compact(pred_parsed):
                        field_metrics[field_label]["tp"] += 1
                        continue

                # Genuine mismatch → count FP and FN
                if pred_norm:
                    field_metrics[field_label]["fp"] += 1
                if gt_norm:
                    field_metrics[field_label]["fn"] += 1

    # ── Score unmatched GT slots (missed by model → FN for all fields) ──
    for slot_idx, slot in enumerate(unmatched_slots):
        offset = len(pairs) + slot_idx
        gt = gt_entities[offset] if offset < len(gt_entities) else {}
        for field_label, _, _, normalizer in _EVAL_FIELD_DEFS:
            gt_val_candidate = _expected_value_from_slot_or_gt(field_label, slot, gt)
            if gt_val_candidate is None:
                continue
            gt_val = _to_text(gt_val_candidate)
            if field_label == "driver":
                gt_val = _sanitize_driver_value(gt_val)
            gt_norm = normalizer(gt_val)
            if gt_norm:
                field_metrics[field_label]["fn"] += 1

    # ── Score extra/duplicate model rows (hallucinations → FP) ──
    for idx in sorted(extra_indices | duplicate_indices):
        if idx not in prepared.index:
            continue
        row = prepared.loc[idx]
        for field_label, _, model_col, normalizer in _EVAL_FIELD_DEFS:
            pred_val = _to_text(row.get(model_col, ""))
            pred_norm = normalizer(pred_val)
            if pred_norm:
                field_metrics[field_label]["fp"] += 1

    # ── Add status_unit as a special field ──
    status_metrics = {"tp": 0, "fp": 0, "fn": 0}
    for pair_idx, pair in enumerate(pairs):
        row = pair["row"]
        slot = pair.get("slot") or {}
        gt = gt_entities[pair_idx] if pair_idx < len(gt_entities) else {}
        gt_status = _to_text(slot.get("status") or gt.get("status_unit", "")).upper()
        pred_status = _to_text(row.get("status_norm", "")).upper() or _to_text(row.get("status_unit", "")).upper()

        # ATURAN 1: If GT driver was spill-over, expected status is PARTIAL
        gt_driver = _sanitize_driver_value(
            _to_text(slot.get("driver_raw") or gt.get("driver", ""))
        )
        if not gt_driver:
            gt_status = "PARTIAL"

        if gt_status == pred_status:
            status_metrics["tp"] += 1
        else:
            if pred_status:
                status_metrics["fp"] += 1
            if gt_status:
                status_metrics["fn"] += 1

    for slot in unmatched_slots:
        status_metrics["fn"] += 1
    for idx in sorted(extra_indices | duplicate_indices):
        if idx in prepared.index:
            status_metrics["fp"] += 1

    field_metrics["status_unit"] = status_metrics
    return field_metrics


def _pair_expected_slots(
    expected_slots: List[Dict[str, str]],
    prepared: pd.DataFrame,
    duplicate_indices: set,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    used_indices = set()
    pairs: List[Dict[str, Any]] = []
    unmatched: List[Dict[str, str]] = []

    for slot in expected_slots:
        candidates: List[Tuple[int, int, int, Any]] = []
        for row_idx, row in prepared.iterrows():
            if row_idx in used_indices or row_idx in duplicate_indices:
                continue

            score, identity_hits, structure_hits = _score_expected_slot(slot, row)
            slot_status = _to_text(slot.get("status")).upper()
            row_status = _to_text(row.get("status_norm")).upper()

            if slot_status == "ASSIGNED":
                if _slot_has_identity(slot) and identity_hits == 0:
                    continue
                if not _slot_has_identity(slot) and structure_hits == 0:
                    continue
            else:
                if row_status != "PARTIAL" and _row_has_identity(row):
                    continue
                if score <= 0 or (structure_hits == 0 and row_status != "PARTIAL"):
                    continue

            candidates.append((score, identity_hits, structure_hits, row_idx))

        if not candidates:
            unmatched.append(slot)
            continue

        candidates.sort(
            key=lambda item: (
                -item[0],
                -item[1],
                -item[2],
                int(prepared.loc[item[3], "_audit_row_no"]),
            )
        )
        _, _, _, chosen_idx = candidates[0]
        used_indices.add(chosen_idx)
        pairs.append({"slot": slot, "row_idx": chosen_idx, "row": prepared.loc[chosen_idx]})

    return pairs, unmatched


def _row_brief(row: pd.Series) -> str:
    job = _to_text(row.get("job_number")) or "-"
    driver = _to_text(row.get("driver")) or "-"
    route = _to_text(row.get("tujuan")) or "-"
    return f"Job {job} (Driver: {driver}, Rute: {route})"


def _slot_brief(slot: Dict[str, str]) -> str:
    if slot.get("status") == "PARTIAL":
        return f"{slot.get('slot_id')} berstatus PARTIAL"
    driver = slot.get("driver_raw") or "-"
    route = _display_route(slot.get("route_key"))
    return f"{slot.get('slot_id')}: Driver {driver}, Rute {route}"


def _summarize_rows(prepared: pd.DataFrame, indices: List[Any], limit: int = 3) -> str:
    if not indices:
        return ""
    ordered = sorted(indices, key=lambda idx: int(prepared.loc[idx, "_audit_row_no"]))
    snippets = [_row_brief(prepared.loc[idx]) for idx in ordered[:limit]]
    if len(ordered) > limit:
        snippets.append(f"{len(ordered) - limit} baris lain")
    return "; ".join(snippets)


def _summarize_slots(slots: List[Dict[str, str]], limit: int = 3) -> str:
    if not slots:
        return ""
    snippets = [_slot_brief(slot) for slot in slots[:limit]]
    if len(slots) > limit:
        snippets.append(f"{len(slots) - limit} slot lain")
    return "; ".join(snippets)


def _compute_ml_observability(message_text: str, expected_rows: int, matched_df: pd.DataFrame) -> Dict[str, Any]:
    expected_slots = _extract_expected_slots(message_text, expected_rows)
    prepared = _prepare_rows_for_matching(matched_df)
    if not prepared.empty:
        prepared["_audit_row_no"] = list(range(1, len(prepared) + 1))
    else:
        prepared["_audit_row_no"] = []

    duplicate_indices = _detect_duplicate_rows(prepared) if not prepared.empty else set()
    pairs, unmatched_slots = _pair_expected_slots(expected_slots, prepared, duplicate_indices)
    used_indices = {pair["row_idx"] for pair in pairs}
    extra_indices = set(prepared.index) - used_indices - duplicate_indices

    record_tp = len(pairs)
    record_fp = len(duplicate_indices) + len(extra_indices)
    record_fn = len(unmatched_slots)
    record_scores = _metric_scores(record_tp, record_fp, record_fn)

    record_fp_logs: List[Dict[str, Any]] = []
    if duplicate_indices:
        record_fp_logs.append(
            {
                "count": len(duplicate_indices),
                "title": "BARIS DUPLIKAT",
                "text": f"{_summarize_rows(prepared, list(duplicate_indices))} adalah data duplikat.",
            }
        )
    if extra_indices:
        record_fp_logs.append(
            {
                "count": len(extra_indices),
                "title": "BARIS HALUSINASI",
                "text": f"{_summarize_rows(prepared, list(extra_indices))} tidak punya pasangan di input.",
            }
        )

    record_fn_logs: List[Dict[str, Any]] = []
    if unmatched_slots:
        partial_missing = [slot for slot in unmatched_slots if slot.get("status") == "PARTIAL"]
        assigned_missing = [slot for slot in unmatched_slots if slot.get("status") == "ASSIGNED"]
        if assigned_missing:
            record_fn_logs.append(
                {
                    "count": len(assigned_missing),
                    "title": "BARIS HILANG",
                    "text": f"Kekurangan {len(assigned_missing)} target pesanan ASSIGNED: {_summarize_slots(assigned_missing)}.",
                }
            )
        if partial_missing:
            record_fn_logs.append(
                {
                    "count": len(partial_missing),
                    "title": "BARIS HILANG",
                    "text": f"Kekurangan {len(partial_missing)} target pesanan berstatus PARTIAL.",
                }
            )

    route_tp = 0
    route_fp = 0
    route_fn = 0
    route_fp_details: List[str] = []
    route_fn_details: List[str] = []
    mismatch_predicted_keys: List[str] = []

    for pair in pairs:
        slot = pair["slot"]
        if slot.get("status") != "ASSIGNED":
            continue
        row = pair["row"]
        expected_route = slot.get("route_key") or ""
        predicted_route = _to_text(row.get("route_key"))
        driver = slot.get("driver_raw") or _to_text(row.get("driver")) or "-"

        if expected_route and predicted_route and expected_route == predicted_route:
            route_tp += 1
            continue

        if predicted_route:
            route_fp += 1
            mismatch_predicted_keys.append(predicted_route)
            route_fp_details.append(
                f"Driver <b>{_escape_html(driver)}</b>: Tercetak \"<b>{_escape_html(_to_text(row.get('tujuan')) or '-')}</b>\" -&gt; Seharusnya \"<b>{_escape_html(_display_route(expected_route))}</b>\"."
            )
        if expected_route:
            route_fn += 1
            route_fn_details.append(
                f"Rute asli \"<b>{_escape_html(_display_route(expected_route))}</b>\" untuk driver <b>{_escape_html(driver)}</b> tidak ditemukan."
            )

    assigned_unmatched = [slot for slot in unmatched_slots if slot.get("status") == "ASSIGNED"]
    for slot in assigned_unmatched:
        expected_route = slot.get("route_key") or ""
        if not expected_route:
            continue
        route_fn += 1
        driver_raw = slot.get('driver_raw') or '-'
        route_fn_details.append(
            f"Rute \"<b>{_escape_html(_display_route(expected_route))}</b>\" untuk driver <b>{_escape_html(driver_raw)}</b> tidak ada di output."
        )

    extra_route_indices = [
        idx
        for idx in sorted(duplicate_indices | extra_indices, key=lambda i: int(prepared.loc[i, "_audit_row_no"]))
        if _to_text(prepared.loc[idx].get("route_key")) and (_row_has_identity(prepared.loc[idx]) or _to_text(prepared.loc[idx].get("status_norm")) == "ASSIGNED")
    ]
    for idx in extra_route_indices:
        row = prepared.loc[idx]
        route_fp += 1
        fp_driver = _to_text(row.get('driver')) or '-'
        fp_job = _to_text(row.get('job_number')) or '-'
        fp_route = _to_text(row.get('tujuan')) or '-'
        route_fp_details.append(
            f"Driver <b>{_escape_html(fp_driver)}</b> (Job <b>{_escape_html(fp_job)}</b>) mencetak rute \"<b>{_escape_html(fp_route)}</b>\" yang tidak valid."
        )

    route_scores = _metric_scores(route_tp, route_fp, route_fn)

    route_fp_logs: List[Dict[str, Any]] = []
    mismatch_fps = [d for d in route_fp_details if 'Tercetak' in d]
    halluc_fps = [d for d in route_fp_details if 'tidak valid' in d]
    if mismatch_fps:
        route_fp_logs.append(
            {
                "count": len(mismatch_fps),
                "title": "RUTE SALAH TULIS",
                "text": "<br>".join(mismatch_fps),
                "raw_html": True,
            }
        )
    if halluc_fps:
        route_fp_logs.append(
            {
                "count": len(halluc_fps),
                "title": "RUTE HALUSINASI",
                "text": "<br>".join(halluc_fps),
                "raw_html": True,
            }
        )

    route_fn_logs: List[Dict[str, Any]] = []
    if route_fn_details:
        route_fn_logs.append(
            {
                "count": len(route_fn_details),
                "title": "RUTE HILANG",
                "text": "Sistem gagal menemukan: <br>" + "<br>".join(route_fn_details),
                "raw_html": True,
            }
        )

    analysis = ""
    if mismatch_predicted_keys:
        route_counts: Dict[str, int] = {}
        for route_key in mismatch_predicted_keys:
            route_counts[route_key] = route_counts.get(route_key, 0) + 1
        dominant_route = max(route_counts, key=lambda k: route_counts[k])
        if route_counts[dominant_route] >= 2:
            analysis = (
                "Terjadi indikasi context overwriting: beberapa baris memakai tujuan "
                f"\"{_display_route(dominant_route)}\" walaupun input memiliki tujuan spesifik berbeda."
            )
        else:
            analysis = "Terjadi mismatch konteks tujuan pada baris ASSIGNED; evaluasi slot mencatat FP dan FN secara terpisah."

    # ── Compute per-field slot metrics with business rules ──
    slot_field_metrics = _compute_slot_field_metrics(
        pairs, unmatched_slots, extra_indices, duplicate_indices,
        prepared, message_text,
    )

    return {
        "record": {
            "tp": record_tp,
            "fp": record_fp,
            "fn": record_fn,
            **record_scores,
            "fp_logs": record_fp_logs,
            "fn_logs": record_fn_logs,
        },
        "route": {
            "tp": route_tp,
            "fp": route_fp,
            "fn": route_fn,
            **route_scores,
            "fp_logs": route_fp_logs,
            "fn_logs": route_fn_logs,
            "analysis": analysis,
        },
        "slot_fields": slot_field_metrics,
    }


def _prepare_rows_for_matching(rows_df: pd.DataFrame) -> pd.DataFrame:
    work = rows_df.copy()
    for col in _OUTPUT_COLUMNS:
        if col not in work.columns:
            work[col] = ""

    work["pickup_key"] = work["pickup"].map(_normalize_compact)
    work["route_key"] = work["tujuan"].map(_normalize_route)
    work["unit_key"] = work["type_truck"].map(_normalize_unit_type)
    work["driver_key"] = work["driver"].map(_normalize_name)
    work["plate_key"] = work["no_plat"].map(_normalize_compact)
    work["phone_key"] = work["kontak_driver"].map(_normalize_phone)
    work["status_norm"] = work["status_unit"].fillna("").astype(str).str.upper().str.strip()
    if "order_created_at" not in work.columns:
        work["order_created_at"] = pd.NaT
    work["order_created_at"] = pd.to_datetime(work["order_created_at"], errors="coerce")
    return work


def _score_row(block_payload: Dict[str, Any], row: pd.Series) -> Tuple[int, int, int]:
    score = 0
    identity_hits = 0
    structure_hits = 0

    if block_payload["plate_key"] and row["plate_key"] and block_payload["plate_key"] == row["plate_key"]:
        score += 140
        identity_hits += 1
    if block_payload["phone_key"] and row["phone_key"] and block_payload["phone_key"] == row["phone_key"]:
        score += 120
        identity_hits += 1
    if block_payload["driver_key"] and row["driver_key"] and block_payload["driver_key"] == row["driver_key"]:
        score += 100
        identity_hits += 1

    if block_payload["pickup_key"] and row["pickup_key"] and block_payload["pickup_key"] == row["pickup_key"]:
        score += 70
        structure_hits += 1
    if block_payload["route_key"] and row["route_key"] and block_payload["route_key"] == row["route_key"]:
        score += 70
        structure_hits += 1
    if block_payload["unit_key"] and row["unit_key"] and block_payload["unit_key"] == row["unit_key"]:
        score += 55
        structure_hits += 1

    return score, identity_hits, structure_hits


def _select_rows_for_block(
    prepared: pd.DataFrame,
    available: List[Any],
    message_text: str,
    expected_rows: int,
    payload: Dict[str, Any],
) -> List[Any]:
    if not available or expected_rows <= 0:
        return []

    available_df = prepared.loc[available].copy()
    if available_df.empty:
        return []
    available_df["_audit_row_no"] = list(range(1, len(available_df) + 1))

    # 1) Primary pairing: enforce slot/status/identity consistency.
    expected_slots = _extract_expected_slots(message_text, expected_rows)
    duplicate_indices = _detect_duplicate_rows(available_df)
    pairs, _ = _pair_expected_slots(expected_slots, available_df, duplicate_indices)

    chosen_indices: List[Any] = [
        pair["row_idx"] for pair in pairs if pair.get("row_idx") in available
    ]
    if len(chosen_indices) >= expected_rows:
        return chosen_indices[:expected_rows]

    # 2) Conservative fallback: only take rows without strong identity signal
    # (or rows already PARTIAL) to avoid cross-block identity hijacking.
    chosen_set = set(chosen_indices)
    fallback_candidates: List[Tuple[int, int, Any]] = []
    for row_idx in available:
        if row_idx in chosen_set or row_idx in duplicate_indices:
            continue
        row = available_df.loc[row_idx]
        row_status = _to_text(row.get("status_norm")).upper()
        if row_status != "PARTIAL" and _row_has_identity(row):
            continue
        score, _, structure_hits = _score_row(payload, row)
        if score <= 0 or structure_hits <= 0:
            continue
        fallback_candidates.append((score, structure_hits, row_idx))

    fallback_candidates.sort(
        key=lambda x: (
            -x[0],
            -x[1],
            prepared.loc[x[2], "order_created_at"] if pd.notna(prepared.loc[x[2], "order_created_at"]) else pd.Timestamp.max,
            _to_text(prepared.loc[x[2], "job_number"]),
        )
    )

    for _, _, row_idx in fallback_candidates:
        if row_idx in chosen_set:
            continue
        chosen_indices.append(row_idx)
        chosen_set.add(row_idx)
        if len(chosen_indices) >= expected_rows:
            break

    return chosen_indices


def _status_breakdown(df: pd.DataFrame) -> Tuple[int, int]:
    if df.empty or "status_unit" not in df.columns:
        return 0, 0
    status = df["status_unit"].fillna("").astype(str).str.upper().str.strip()
    assigned = int((status == "ASSIGNED").sum())
    partial = int((status == "PARTIAL").sum())
    return assigned, partial


def _block_has_issue(block: Dict[str, Any]) -> bool:
    audit = block.get("ml_audit") or {}
    record = audit.get("record") or {}
    route = audit.get("route") or {}
    expected_rows = int(block.get("expected_rows") or 0)
    matched_rows = int(block.get("matched_rows") or 0)
    return (
        int(record.get("fp") or 0) > 0
        or int(record.get("fn") or 0) > 0
        or int(route.get("fp") or 0) > 0
        or int(route.get("fn") or 0) > 0
        or expected_rows != matched_rows
    )


def _match_rows_to_messages(rows_df: pd.DataFrame, messages: List[str]) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
    prepared = _prepare_rows_for_matching(rows_df)
    available = list(prepared.index)
    blocks: List[Dict[str, Any]] = []

    for idx, message in enumerate(messages, start=1):
        payload = _extract_block_payload(message)
        partition = _classify_block_partition(message)
        qty = payload.get("qty")
        expected_rows = int(qty) if isinstance(qty, int) and qty > 0 else 1
        chosen_indices = _select_rows_for_block(
            prepared=prepared,
            available=available,
            message_text=message,
            expected_rows=expected_rows,
            payload=payload,
        )
        for row_idx in chosen_indices:
            if row_idx in available:
                available.remove(row_idx)

        matched_df = rows_df.loc[chosen_indices].copy() if chosen_indices else rows_df.iloc[0:0].copy()
        assigned_count, partial_count = _status_breakdown(matched_df)
        ml_audit = _compute_ml_observability(message, expected_rows, matched_df)

        blocks.append(
            {
                "block_index": idx,
                "message_text": message,
                "expected_rows": expected_rows,
                "matched_rows": int(matched_df.shape[0]),
                "assigned_count": assigned_count,
                "partial_count": partial_count,
                "matched_df": matched_df,
                "ml_audit": ml_audit,
                "partition_domain": _to_text(partition.get("domain")),
                "partition_subtype": _to_text(partition.get("subtype")),
                "partition_reason": _to_text(partition.get("reason")),
            }
        )

    unmatched_df = rows_df.loc[available].copy() if available else rows_df.iloc[0:0].copy()
    return blocks, unmatched_df


def _to_display_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    safe = df.copy()
    for col in _OUTPUT_COLUMNS:
        if col not in safe.columns:
            safe[col] = ""
    safe = safe[_OUTPUT_COLUMNS].copy()
    safe = safe.rename(columns=_OUTPUT_LABELS)
    return safe.fillna("")


def _style_status_rows(df: pd.DataFrame):
    if df.empty or "Status Unit" not in df.columns:
        return df

    def _status_row_style(row: pd.Series) -> List[str]:
        status = str(row.get("Status Unit", "")).strip().upper()
        if status == "ASSIGNED":
            return ["background-color: rgba(34, 197, 94, 0.14); color: #000000;"] * len(row)
        if status == "PARTIAL":
            return ["background-color: rgba(250, 204, 21, 0.22); color: #000000;"] * len(row)
        return [""] * len(row)

    return df.style.apply(_status_row_style, axis=1)


def _escape_html(value: Any) -> str:
    return html.escape(_to_text(value), quote=True)


def _to_int_safe(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except Exception:
        return 0


def _render_global_kpi_strip(batch_df: pd.DataFrame) -> None:
    total_batches = int(batch_df.shape[0])
    total_rows = _to_int_safe(batch_df.get("output_rows", pd.Series(dtype="int64")).fillna(0).sum())
    total_assigned = _to_int_safe(batch_df.get("assigned_rows", pd.Series(dtype="int64")).fillna(0).sum())
    total_partial = _to_int_safe(batch_df.get("partial_rows", pd.Series(dtype="int64")).fillna(0).sum())
    assign_rate = (total_assigned / total_rows) if total_rows else 0.0

    kpi_html = (
        '<div class="kpi-grid">'
        '<div class="kpi-card"><div class="kpi-label">Total Batch</div>'
        f'<div class="kpi-value">{total_batches}</div></div>'
        '<div class="kpi-card"><div class="kpi-label">Total Output Row</div>'
        f'<div class="kpi-value">{total_rows}</div></div>'
        '<div class="kpi-card"><div class="kpi-label">Assigned</div>'
        f'<div class="kpi-value">{total_assigned}</div></div>'
        '<div class="kpi-card"><div class="kpi-label">Partial</div>'
        f'<div class="kpi-value">{total_partial}</div></div>'
        '<div class="kpi-card"><div class="kpi-label">Assigned Rate</div>'
        f'<div class="kpi-value">{assign_rate * 100:.1f}%</div></div>'
        "</div>"
    )
    st.markdown(kpi_html, unsafe_allow_html=True)


def _log_rows_html(logs: List[Dict[str, Any]], label: str, class_name: str) -> str:
    rows: List[str] = []
    for log in logs:
        count = int(log.get("count") or 0)
        title = _escape_html(log.get("title"))
        is_raw = bool(log.get("raw_html"))
        text_value = log.get("text", "") if is_raw else _escape_html(log.get("text"))
        rows.append(
            f"<div class='ml-log-row {class_name}'>"
            f"<span class='ml-tag'>[{label} +{count}]</span> "
            f"<b>{title}:</b> {text_value}"
            "</div>"
        )
    return "".join(rows)


def _metric_section_html(title: str, subtitle: str, metrics: Dict[str, Any]) -> str:
    fp_logs = metrics.get("fp_logs", [])
    fn_logs = metrics.get("fn_logs", [])
    logs_html = _log_rows_html(fp_logs, "FP", "ml-log-fp") + _log_rows_html(fn_logs, "FN", "ml-log-fn")
    if not logs_html:
        logs_html = (
            "<div class='ml-log-row ml-log-ok'>"
            "<span class='ml-tag'>[OK]</span> Tidak ada FP atau FN pada level evaluasi ini."
            "</div>"
        )

    analysis = _to_text(metrics.get("analysis"))
    analysis_html = ""
    if analysis:
        analysis_html = (
            "<div class='ml-analysis'>"
            f"<span class='ml-tag'>[ANALYSIS]</span> {_escape_html(analysis)}"
            "</div>"
        )

    tp = int(metrics.get("tp") or 0)
    fp = int(metrics.get("fp") or 0)
    fn = int(metrics.get("fn") or 0)
    precision = _display_pct(float(metrics.get("precision") or 0.0))
    recall = _display_pct(float(metrics.get("recall") or 0.0))
    f1 = _display_pct(float(metrics.get("f1") or 0.0))

    return (
        '<div class="ml-metric-section">'
        f'<div class="ml-metric-title">{_escape_html(title)} '
        f'<span class="ml-metric-subtitle">{_escape_html(subtitle)}</span></div>'
        '<div class="ml-metric-stat-line">'
        f"TP: <strong>{tp}</strong> &nbsp;|&nbsp; "
        f"FP: <strong>{fp}</strong> &nbsp;|&nbsp; "
        f"FN: <strong>{fn}</strong><br>"
        f"Precision: <strong>{precision}</strong> &nbsp;|&nbsp; "
        f"Recall: <strong>{recall}</strong> &nbsp;|&nbsp; "
        f"F1-Score: <strong>{f1}</strong>"
        "</div>"
        '<div class="ml-log-title">Reason</div>'
        f"{logs_html}"
        f"{analysis_html}"
        "</div>"
    )


def _render_ml_observability_card(block: Dict[str, Any]) -> None:
    audit = block.get("ml_audit") or {}
    record = audit.get("record") or {}
    route = audit.get("route") or {}
    record_f1 = float(record.get("f1") or 0.0)
    route_f1 = float(route.get("f1") or 0.0)
    batch_label = _escape_html(block.get("batch_label") or f"BLOCK #{int(block.get('block_index') or 0)}")

    record_section = _metric_section_html("1. RECORD-LEVEL METRICS", "(Evaluasi Baris)", record)
    route_section = _metric_section_html("2. FIELDS-LEVEL METRICS", "(Evaluasi Fields)", route)

    card_html = (
        '<div class="ml-audit-card">'
        "<details open>"
        "<summary>"
        '<div class="ml-audit-summary">'
        f'<div class="ml-audit-title">EVALUASI MODEL &mdash; {batch_label}</div>'
        '<div class="ml-audit-pills">'
        f'<span class="ml-score-pill {_score_class(record_f1)}">RECORD INTEGRITY: {_display_pct(record_f1)}</span>'
        f'<span class="ml-score-pill {_score_class(route_f1)}">ROUTE ACCURACY: {_display_pct(route_f1)}</span>'
        "</div>"
        '<div class="ml-audit-toggle">'
        '<span class="ml-toggle-closed">Lihat Detail</span>'
        '<span class="ml-toggle-open">Tutup</span>'
        "</div>"
        "</div>"
        "</summary>"
        '<div class="ml-audit-body">'
        f"{record_section}"
        f"{route_section}"
        "</div>"
        "</details>"
        "</div>"
    )

    st.markdown(card_html, unsafe_allow_html=True)


def _render_batch_summary_card(
    batch_metrics: Dict[str, Any],
    chat_created_at: str,
    batch_blocks_data: List[Dict[str, Any]],
    title: Optional[str] = None,
) -> None:
    """Render a micro-averaged batch summary card with per-field slot table."""
    _ = chat_created_at
    rec = batch_metrics.get("record") or {}
    slot = batch_metrics.get("slot") or {}
    total_blocks = int(batch_metrics.get("total_blocks") or 0)
    rec_f1 = float(rec.get("f1") or 0.0)
    route_f1 = float(slot.get("f1") or 0.0)
    card_title = _to_text(title) or f"METRICS KUMULATIF BATCH ({total_blocks} BLOK)"

    def _fmt(v: float) -> str:
        return _display_pct(v)

    def _f1_cls(v: float) -> str:
        if v >= 0.8:
            return "ml-slot-f1-good"
        if v >= 0.5:
            return "ml-slot-f1-warn"
        return "ml-slot-f1-bad"

    # --- Build per-field slot data ---
    # Use actual route metrics for "Tujuan"; other fields use matched-pair counts.
    rec_tp = int(rec.get("tp") or 0)
    slot_tp_actual = int(slot.get("tp") or 0)
    slot_fp_actual = int(slot.get("fp") or 0)
    slot_fn_actual = int(slot.get("fn") or 0)

    # ── Build per-field slot data from actual per-field metrics ──
    # Aggregate slot_field_metrics across all blocks if available,
    # otherwise fall back to the old heuristic (rec_tp as baseline).
    agg_fields: Dict[str, Dict[str, int]] = {}
    has_field_data = False
    for block in batch_blocks_data:
        sf = block.get("slot_field_metrics")
        if not sf:
            continue
        has_field_data = True
        for field_name, counts in sf.items():
            if field_name not in agg_fields:
                agg_fields[field_name] = {"tp": 0, "fp": 0, "fn": 0}
            agg_fields[field_name]["tp"] += int(counts.get("tp", 0))
            agg_fields[field_name]["fp"] += int(counts.get("fp", 0))
            agg_fields[field_name]["fn"] += int(counts.get("fn", 0))

    # Map internal field keys to display labels
    _FIELD_DISPLAY = [
        ("tgl_ro",        "Tgl RO"),
        ("tgl_muat",      "Tgl Muat"),
        ("pickup",        "Pickup"),
        ("tujuan",        "Tujuan"),
        ("type_truck",    "Type Truck"),
        ("driver",        "Driver"),
        ("nopol",         "No. Plat"),
        ("kontak_driver", "Kontak Driver"),
        ("status_unit",   "Status Unit"),
    ]

    if has_field_data:
        slot_fields: List[Tuple[str, int, int, int]] = []
        for key, label in _FIELD_DISPLAY:
            f = agg_fields.get(key, {"tp": 0, "fp": 0, "fn": 0})
            slot_fields.append((label, f["tp"], f["fp"], f["fn"]))
    else:
        # Fallback: old heuristic (no per-field data available)
        slot_fields = [
            ("Tgl RO",         rec_tp, 0, 0),
            ("Tgl Muat",       rec_tp, 0, 0),
            ("Pickup",         rec_tp, 0, 0),
            ("Tujuan",         slot_tp_actual, slot_fp_actual, slot_fn_actual),
            ("Type Truck",     rec_tp, 0, 0),
            ("Driver",         rec_tp, 0, 0),
            ("No. Plat",       rec_tp, 0, 0),
            ("Kontak Driver",  rec_tp, 0, 0),
        ]

    # Build table rows
    table_rows = ""
    total_tp = total_fp = total_fn = 0
    for label, tp, fp, fn in slot_fields:
        total_tp += tp
        total_fp += fp
        total_fn += fn
        scores = _metric_scores(tp, fp, fn)
        f1_cls = _f1_cls(scores["f1"])
        table_rows += (
            "<tr>"
            f'<td class="field-name">{_escape_html(label)}</td>'
            f'<td class="num">{tp}</td>'
            f'<td class="num">{fp}</td>'
            f'<td class="num">{fn}</td>'
            f'<td class="num">{_fmt(scores["precision"])}</td>'
            f'<td class="num">{_fmt(scores["recall"])}</td>'
            f'<td class="num {f1_cls}">{_fmt(scores["f1"])}</td>'
            "</tr>"
        )

    # Total row (micro-averaged)
    total_scores = _metric_scores(total_tp, total_fp, total_fn)
    total_f1 = total_scores["f1"]
    total_f1_cls = _f1_cls(total_f1)
    table_rows += (
        '<tr class="row-total">'
        '<td class="field-name">TOTAL KUMULATIF</td>'
        f'<td class="num">{total_tp}</td>'
        f'<td class="num">{total_fp}</td>'
        f'<td class="num">{total_fn}</td>'
        f'<td class="num">{_fmt(total_scores["precision"])}</td>'
        f'<td class="num">{_fmt(total_scores["recall"])}</td>'
        f'<td class="num {total_f1_cls}">{_fmt(total_f1)}</td>'
        "</tr>"
    )

    slot_table_html = (
        '<div class="ml-metric-section ml-batch-slot-section">'
        '<div class="ml-section-title">SLOT METRICS '
        '<span class="ml-section-subtitle">(Kumulatif per Field)</span></div>'
        '<div class="ml-slot-wrap">'
        '<table class="ml-slot-table">'
        "<thead><tr>"
        "<th>Atribut / Field</th>"
        '<th class="num">TP</th>'
        '<th class="num">FP</th>'
        '<th class="num">FN</th>'
        '<th class="num">Precision</th>'
        '<th class="num">Recall</th>'
        '<th class="num">F1-Score</th>'
        "</tr></thead>"
        f"<tbody>{table_rows}</tbody>"
        "</table></div></div>"
    )

    card_html = (
        '<div class="ml-audit-card ml-batch-summary-card" style="margin-top:0.6rem;">'
        '<div class="ml-audit-summary" style="background:#f3f4f6;">'
        f'<div class="ml-audit-title">{_escape_html(card_title)}</div>'
        '<div class="ml-audit-pills">'
        f'<span class="ml-score-pill ml-batch-score-pill {_score_class(rec_f1)}">Record F1: {_fmt(rec_f1)}</span>'
        f'<span class="ml-score-pill ml-batch-score-pill {_score_class(route_f1)}">Route F1: {_fmt(route_f1)}</span>'
        f'<span class="ml-score-pill ml-batch-score-pill {_score_class(total_f1)}">Field Slot F1: {_fmt(total_f1)}</span>'
        "</div>"
        "</div>"
        '<div class="ml-audit-body">'
        '<div class="ml-metric-section">'
        '<div class="ml-stat-line ml-batch-stat-line">'
        f"Record TP: <strong>{rec.get('tp',0)}</strong> &nbsp;|&nbsp; "
        f"FP: <strong>{rec.get('fp',0)}</strong> &nbsp;|&nbsp; "
        f"FN: <strong>{rec.get('fn',0)}</strong> &nbsp;|&nbsp; "
        f"Precision: <strong>{_fmt(rec.get('precision',0))}</strong> &nbsp;|&nbsp; "
        f"Recall: <strong>{_fmt(rec.get('recall',0))}</strong> &nbsp;|&nbsp; "
        f"F1: <strong>{_fmt(rec_f1)}</strong>"
        "</div>"
        "</div>"
        f"{slot_table_html}"
        "</div>"
        "</div>"
    )

    st.markdown(card_html, unsafe_allow_html=True)


def _build_batch_blocks_data(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    batch_blocks_data: List[Dict[str, Any]] = []
    for block in blocks:
        audit = block.get("ml_audit") or {}
        rec = audit.get("record") or {}
        route = audit.get("route") or {}
        batch_blocks_data.append(
            {
                "block_id": block.get("block_index"),
                "record_metrics": {"tp": rec.get("tp", 0), "fp": rec.get("fp", 0), "fn": rec.get("fn", 0)},
                "slot_metrics": {"tp": route.get("tp", 0), "fp": route.get("fp", 0), "fn": route.get("fn", 0)},
                "slot_field_metrics": audit.get("slot_fields"),
            }
        )
    return batch_blocks_data


def _prepare_batch_artifacts(raw_chat_row: pd.Series, rows_df: pd.DataFrame) -> Dict[str, Any]:
    chat_text = _to_text(raw_chat_row.get("chat_text"))
    messages = _split_wa_messages(chat_text)
    blocks, unmatched_df = _match_rows_to_messages(rows_df, messages)
    batch_blocks_data = _build_batch_blocks_data(blocks)
    return {
        "messages": messages,
        "blocks": blocks,
        "unmatched_df": unmatched_df,
        "batch_blocks_data": batch_blocks_data,
    }


def _render_batch_block(
    raw_chat_row: pd.Series,
    rows_df: pd.DataFrame,
    artifacts: Optional[Dict[str, Any]] = None,
) -> bool:
    raw_chat_id = _to_text(raw_chat_row.get("raw_chat_id"))
    chat_created_at = _format_timestamp(raw_chat_row.get("chat_created_at"))
    artifacts = artifacts or _prepare_batch_artifacts(raw_chat_row, rows_df)
    messages = artifacts.get("messages") or []
    blocks = artifacts.get("blocks") or []
    unmatched_df = artifacts.get("unmatched_df")
    if unmatched_df is None:
        unmatched_df = rows_df.iloc[0:0].copy()
    batch_blocks_data = artifacts.get("batch_blocks_data") or _build_batch_blocks_data(blocks)

    batch_assigned = int(raw_chat_row.get("assigned_rows") or 0)
    batch_partial = int(raw_chat_row.get("partial_rows") or 0)
    batch_rows = int(raw_chat_row.get("output_rows") or 0)

    if not blocks:
        return False

    header = (
        f"Batch {raw_chat_id[:8]} | {chat_created_at} | NEW ORDER (NER) | "
        f"Blok Domain: {len(blocks)} / Total Blok: {len(messages)} | Output: {batch_rows} "
        f"(A:{batch_assigned} / P:{batch_partial})"
    )

    with st.expander(header, expanded=False):
        if batch_blocks_data:
            st.markdown("<div class='block-title'>Metrics Kumulatif</div>", unsafe_allow_html=True)
            batch_metrics = calculate_batch_micro_metrics(batch_blocks_data)
            _render_batch_summary_card(batch_metrics, chat_created_at, batch_blocks_data)

        with st.expander("Tampilkan Detail Analitik", expanded=False):
            detail_filter = st.selectbox(
                "Filter Detail",
                options=["All", "Bermasalah"],
                index=0,
                key=f"audit_detail_filter_{raw_chat_id}",
                help="Tampilkan semua blok atau hanya blok dengan masalah pada detail input-output.",
            )

            if detail_filter == "Bermasalah":
                blocks_to_render = [block for block in blocks if _block_has_issue(block)]
            else:
                blocks_to_render = blocks

            st.markdown(
                (
                    "<div class='batch-headline'>"
                    f"<span class='mini-chip'>Raw Chat ID: {_escape_html(raw_chat_id[:12])}</span>"
                    f"<span class='mini-chip'>Created: {_escape_html(chat_created_at)}</span>"
                    f"<span class='mini-chip'>Blok Domain: {len(blocks)}</span>"
                    f"<span class='mini-chip'>Total Blok: {len(messages)}</span>"
                    f"<span class='mini-chip'>Output: {batch_rows} (A:{batch_assigned} / P:{batch_partial})</span>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            if detail_filter == "Bermasalah" and not blocks_to_render:
                st.info("Tidak ada blok bermasalah pada batch ini.")

            for block in blocks_to_render:
                block["batch_label"] = f"BATCH {chat_created_at}"
                has_issue = _block_has_issue(block)
                issue_badge = " <span class='ml-problem-badge'>MASALAH</span>" if has_issue else ""
                st.markdown(
                    (
                        "<div class='block-title'>"
                        f"Block #{int(block.get('block_index') or 0)} "
                        f"| Input: {int(block.get('expected_rows') or 0)} "
                        f"| Output: {int(block.get('matched_rows') or 0)}"
                        f"{issue_badge}"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )

                tab_io, tab_audit = st.tabs(["Input & Output", "Audit Metrics"])

                with tab_io:
                    io_col_input, io_col_output = st.columns(2, gap="small")
                    with io_col_input:
                        st.caption("Input")
                        st.code(block["message_text"], language="text")
                    with io_col_output:
                        st.caption("Output")
                        block_table = _to_display_table(block["matched_df"])
                        if block_table.empty:
                            st.caption("Output belum cocok untuk blok ini.")
                        else:
                            st.dataframe(_style_status_rows(block_table), use_container_width=True, height=230)

                with tab_audit:
                    _render_ml_observability_card(block)

                st.markdown("---")

            if not unmatched_df.empty:
                with st.expander("Output belum terpasang ke blok chat", expanded=False):
                    st.dataframe(_style_status_rows(_to_display_table(unmatched_df)), use_container_width=True, height=230)

    return True


def render_batch_audit_feed(engine_or_conn: Any) -> None:
    _inject_styles()

    st.markdown("<div class='batch-title'>Audit Batch Chat -> Output</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.1, 1.6, 0.8], gap="small")
    with col1:
        batch_limit = st.selectbox(
            "Jumlah Batch",
            options=_BATCH_LIMIT_OPTIONS,
            index=_BATCH_LIMIT_OPTIONS.index(25),
            key="audit_batch_limit",
        )
    with col2:
        st.write("")
    with col3:
        st.write(" ")
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    try:
        batch_df = _read_sql(engine_or_conn, _SQL_BATCH_UPLOADS, {"batch_limit": int(batch_limit)})
    except Exception as exc:
        st.error(f"Gagal membaca batch audit: {exc}")
        return

    if batch_df.empty:
        st.info("Belum ada data pada raw_chats/order_dataset.")
        return

    _render_global_kpi_strip(batch_df)

    batch_payloads: List[Tuple[pd.Series, pd.DataFrame]] = []
    for _, row in batch_df.iterrows():
        raw_chat_id = _to_text(row.get("raw_chat_id"))
        if not raw_chat_id:
            continue
        try:
            rows_df = _read_sql(engine_or_conn, _SQL_BATCH_ROWS, {"raw_chat_id": raw_chat_id})
        except Exception as exc:
            st.error(f"Gagal memuat output untuk batch {raw_chat_id}: {exc}")
            continue
        batch_payloads.append((row.copy(), rows_df.copy()))

    if not batch_payloads:
        st.info("Tidak ada batch yang dapat dirender.")
        return

    rendered_count = 0
    for row, rows_df in batch_payloads:
        rendered = _render_batch_block(
            raw_chat_row=row,
            rows_df=rows_df,
        )
        if rendered:
            rendered_count += 1
    if rendered_count <= 0:
        st.info("Tidak ada blok yang dapat ditampilkan pada rentang batch ini.")


def render_global_audit_feed(engine_or_conn: Any) -> None:
    render_batch_audit_feed(engine_or_conn)


def render_ai_audit_dashboard(engine_or_conn: Any) -> None:
    render_batch_audit_feed(engine_or_conn)


def main() -> None:
    from db.database import engine

    st.set_page_config(page_title="Batch Audit Feed", layout="wide")
    render_batch_audit_feed(engine)


if __name__ == "__main__":
    main()
