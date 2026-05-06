from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine


_NULL_LIKE = {"", "-", "none", "null", "nan", "undefined", "nat"}

_DEFAULT_LINEAGE_LIMIT = 50
_LINEAGE_BATCH_OPTIONS = [25, 50, 100]

_STEP_TABLE_COLUMNS = [
    "unit_key",
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

_STEP_COLUMN_LABELS = {
    "unit_key": "Unit Key",
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

_SQL_BATCH_SEED = """
WITH latest_jobs AS (
    SELECT
        od.job_number,
        MAX(COALESCE(rc.created_at, od.created_at)) AS latest_activity_at
    FROM order_dataset od
    LEFT JOIN raw_chats rc
        ON rc.id = od.raw_chat_id
    WHERE COALESCE(NULLIF(BTRIM(od.job_number), ''), '') <> ''
    GROUP BY od.job_number
    ORDER BY latest_activity_at DESC, od.job_number DESC
    LIMIT :seed_job_limit
)
SELECT
    od.id::text AS order_row_id,
    od.raw_chat_id::text AS raw_chat_id,
    od.row_hash,
    od.job_number,
    od.tgl_ro,
    od.tgl_muat,
    od.pickup,
    od.tujuan,
    od.no_plat,
    od.type_truck,
    od.driver,
    od.kontak_driver,
    od.status_unit,
    od.created_at AS order_created_at,
    rc.id::text AS chat_id,
    rc.chat_hash,
    rc.chat_text,
    rc.created_at AS chat_created_at,
    lj.latest_activity_at
FROM latest_jobs lj
INNER JOIN order_dataset od
    ON od.job_number = lj.job_number
LEFT JOIN raw_chats rc
    ON rc.id = od.raw_chat_id
ORDER BY
    lj.latest_activity_at DESC,
    COALESCE(rc.created_at, od.created_at) ASC,
    od.created_at ASC,
    od.id ASC
"""


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .audit-title {
            padding: 0.72rem 0.95rem;
            border-radius: 0.85rem;
            border: 1px solid rgba(120, 156, 246, 0.34);
            background: linear-gradient(120deg, rgba(27, 48, 96, 0.30), rgba(34, 94, 148, 0.12));
            font-weight: 700;
            letter-spacing: 0.2px;
            margin-bottom: 0.35rem;
        }
        .audit-subtitle {
            color: rgba(216, 225, 245, 0.86);
            margin-bottom: 1rem;
        }
        .audit-chip {
            display: inline-block;
            padding: 0.18rem 0.55rem;
            margin: 0.05rem 0.35rem 0.45rem 0;
            border-radius: 999px;
            border: 1px solid rgba(120, 156, 246, 0.35);
            background: rgba(74, 109, 196, 0.13);
            font-size: 0.80rem;
        }
        .tag-new {
            display: inline-block;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            border: 1px solid rgba(75, 182, 117, 0.52);
            background: rgba(63, 166, 105, 0.18);
            color: #8df0b7;
            font-size: 0.78rem;
            font-weight: 620;
        }
        .tag-revision {
            display: inline-block;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            border: 1px solid rgba(224, 167, 43, 0.50);
            background: rgba(171, 123, 27, 0.20);
            color: #ffd887;
            font-size: 0.78rem;
            font-weight: 620;
        }
        .delta-note {
            color: rgba(233, 237, 245, 0.86);
            font-size: 0.86rem;
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


def _normalize_cell(value: Any) -> str:
    return "NULL" if _is_blank(value) else _to_text(value)


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


class _DisjointSet:
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}
        self.size: Dict[str, int] = {}

    def add(self, node: str) -> None:
        if node in self.parent:
            return
        self.parent[node] = node
        self.size[node] = 1

    def find(self, node: str) -> str:
        if node not in self.parent:
            self.add(node)
        root = node
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[node] != node:
            parent = self.parent[node]
            self.parent[node] = root
            node = parent
        return root

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        left_size = self.size[left_root]
        right_size = self.size[right_root]
        if left_size < right_size:
            left_root, right_root = right_root, left_root
            left_size, right_size = right_size, left_size
        self.parent[right_root] = left_root
        self.size[left_root] = left_size + right_size
        self.size.pop(right_root, None)


def _coerce_datetimes(df: pd.DataFrame) -> pd.DataFrame:
    safe = df.copy()
    for col in ("latest_activity_at", "order_created_at", "chat_created_at"):
        if col in safe.columns:
            safe[col] = pd.to_datetime(safe[col], errors="coerce")
    safe["event_ts"] = safe["chat_created_at"].combine_first(safe["order_created_at"])
    return safe


def _prepare_seed_feed(engine_or_conn: Any, lineage_limit: int) -> pd.DataFrame:
    seed_multiplier = 6
    seed_job_limit = max(int(lineage_limit) * seed_multiplier, _DEFAULT_LINEAGE_LIMIT * 3)
    df = _read_sql(engine_or_conn, _SQL_BATCH_SEED, {"seed_job_limit": seed_job_limit})
    if df.empty:
        return df

    df = _coerce_datetimes(df)
    df["job_number"] = df["job_number"].fillna("").astype(str).str.strip()
    df["raw_chat_id"] = df["raw_chat_id"].fillna("").astype(str).str.strip()
    df["chat_text"] = df["chat_text"].fillna("").astype(str)
    return df[df["job_number"] != ""].copy()


def _assign_lineage_components(feed_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if feed_df.empty:
        return feed_df.copy(), pd.DataFrame()

    work = feed_df.copy()
    dsu = _DisjointSet()

    for job in work["job_number"].dropna().astype(str).str.strip().tolist():
        if job:
            dsu.add(f"job::{job}")

    for _, row in work.iterrows():
        job = _to_text(row.get("job_number"))
        chat = _to_text(row.get("raw_chat_id"))
        if not job:
            continue
        job_node = f"job::{job}"
        dsu.add(job_node)
        if chat:
            chat_node = f"chat::{chat}"
            dsu.add(chat_node)
            dsu.union(job_node, chat_node)

    lineage_roots: List[str] = []
    for _, row in work.iterrows():
        job = _to_text(row.get("job_number"))
        if not job:
            lineage_roots.append(f"row::{_to_text(row.get('order_row_id'))}")
            continue
        lineage_roots.append(dsu.find(f"job::{job}"))
    work["lineage_root"] = lineage_roots

    meta = (
        work.groupby("lineage_root", sort=False, as_index=False)
        .agg(
            latest_activity_at=("event_ts", "max"),
            row_count=("order_row_id", "nunique"),
            chat_count=(
                "raw_chat_id",
                lambda s: int(s.astype(str).str.strip().replace("", pd.NA).dropna().nunique()),
            ),
            job_count=("job_number", "nunique"),
        )
        .sort_values(by=["latest_activity_at", "lineage_root"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )

    meta["lineage_id"] = ["LINEAGE-%04d" % (idx + 1) for idx in range(len(meta))]
    lineage_map = dict(zip(meta["lineage_root"], meta["lineage_id"]))
    work["lineage_id"] = work["lineage_root"].map(lineage_map)
    return work, meta


def _prepare_step_table(event_rows: pd.DataFrame) -> pd.DataFrame:
    step_df = event_rows.copy()
    step_df["unit_key"] = step_df["row_hash"].fillna("").astype(str).str.strip()
    missing_key = step_df["unit_key"] == ""
    step_df.loc[missing_key, "unit_key"] = (
        step_df.loc[missing_key, "job_number"].fillna("").astype(str).str.strip()
        + "#"
        + step_df.loc[missing_key, "order_row_id"].fillna("").astype(str)
    )

    for col in _STEP_TABLE_COLUMNS:
        if col not in step_df.columns:
            step_df[col] = ""

    step_df = step_df[_STEP_TABLE_COLUMNS].copy()
    step_df = step_df.sort_values(by=["job_number", "unit_key"], ascending=[True, True], kind="stable")
    step_df = step_df.set_index("unit_key", drop=True)
    step_df = step_df.apply(lambda col: col.map(_normalize_cell))
    step_df = step_df.rename(columns=_STEP_COLUMN_LABELS)
    step_df.index.name = "Unit Key"
    return step_df


def _build_delta_styler(current_df: pd.DataFrame, previous_df: pd.DataFrame) -> pd.io.formats.style.Styler:
    curr = current_df.copy()
    prev = previous_df.copy()
    prev_aligned = prev.reindex(index=curr.index, columns=curr.columns).fillna("NULL")
    new_row_mask = ~curr.index.isin(prev.index)

    style_matrix = pd.DataFrame("", index=curr.index, columns=curr.columns)
    for col in curr.columns:
        curr_vals = curr[col].astype(str)
        prev_vals = prev_aligned[col].astype(str)
        changed_mask = curr_vals != prev_vals
        for row_pos, row_key in enumerate(curr.index):
            if not changed_mask.iloc[row_pos]:
                continue
            if new_row_mask[row_pos]:
                style_matrix.at[row_key, col] = "background-color: rgba(78, 190, 120, 0.30);"
            else:
                style_matrix.at[row_key, col] = "background-color: rgba(240, 187, 76, 0.34);"

    return curr.style.apply(lambda _: style_matrix, axis=None)


def _build_lineage_events(lineage_df: pd.DataFrame) -> List[Dict[str, Any]]:
    if lineage_df.empty:
        return []

    work = lineage_df.copy()
    work = work.sort_values(
        by=["event_ts", "order_created_at", "order_row_id"],
        ascending=[True, True, True],
        kind="stable",
    )
    work["event_key"] = work["raw_chat_id"].fillna("").astype(str).str.strip()
    empty_key = work["event_key"] == ""
    work.loc[empty_key, "event_key"] = "__order_only__:" + work.loc[empty_key, "order_row_id"].astype(str)

    events: List[Dict[str, Any]] = []
    previous_table: Optional[pd.DataFrame] = None

    grouped = work.groupby("event_key", sort=False, dropna=False)
    for step_idx, (_, event_rows) in enumerate(grouped, start=1):
        event_rows = event_rows.sort_values(
            by=["order_created_at", "order_row_id"],
            ascending=[True, True],
            kind="stable",
        )

        event_ts = event_rows["event_ts"].min() if "event_ts" in event_rows.columns else None
        chat_text = "-"
        chat_hash = "-"
        raw_chat_id = _to_text(event_rows["raw_chat_id"].iloc[0]) if "raw_chat_id" in event_rows.columns else ""

        if "chat_text" in event_rows.columns and event_rows["chat_text"].astype(str).str.strip().ne("").any():
            chat_text = _to_text(event_rows.loc[event_rows["chat_text"].astype(str).str.strip().ne(""), "chat_text"].iloc[0])
        if "chat_hash" in event_rows.columns and event_rows["chat_hash"].astype(str).str.strip().ne("").any():
            chat_hash = _to_text(event_rows.loc[event_rows["chat_hash"].astype(str).str.strip().ne(""), "chat_hash"].iloc[0])

        step_table = _prepare_step_table(event_rows)
        styled = step_table.style
        delta_mode = "none"
        if previous_table is not None:
            styled = _build_delta_styler(step_table, previous_table)
            delta_mode = "changed"

        events.append(
            {
                "step_index": step_idx,
                "step_type": "NEW ORDER" if step_idx == 1 else "REVISED/MERGED",
                "timestamp": _format_timestamp(event_ts),
                "raw_chat_id": raw_chat_id or "-",
                "chat_hash": chat_hash or "-",
                "chat_text": chat_text or "-",
                "table": step_table,
                "styled_table": styled,
                "delta_mode": delta_mode,
                "row_count": int(step_table.shape[0]),
            }
        )
        previous_table = step_table.copy()

    return events


def _render_lineage_block(lineage_id: str, lineage_df: pd.DataFrame, latest_activity: Any) -> int:
    events = _build_lineage_events(lineage_df)
    if not events:
        return 0

    jobs = sorted(lineage_df["job_number"].dropna().astype(str).str.strip().unique().tolist())
    latest_ts = _format_timestamp(latest_activity)
    header = f"{lineage_id} | Jobs: {len(jobs)} | Events: {len(events)} | Last Activity: {latest_ts}"

    with st.expander(header, expanded=False):
        st.markdown(
            "<span class='audit-chip'>Lineage grouping: connected job_number <-> raw_chat_id</span>"
            "<span class='audit-chip'>Left: Input Chat</span>"
            "<span class='audit-chip'>Right: Output Batch Table</span>",
            unsafe_allow_html=True,
        )
        st.caption("Job numbers in lineage: " + ", ".join(jobs))

        for event in events:
            if event["step_type"] == "NEW ORDER":
                st.markdown("<span class='tag-new'>STEP NEW ORDER</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='tag-revision'>STEP REVISED/MERGED</span>", unsafe_allow_html=True)
            st.caption(
                f"Step {event['step_index']} | Time: {event['timestamp']} | "
                f"raw_chat_id: {event['raw_chat_id']} | rows: {event['row_count']}"
            )

            left_col, right_col = st.columns([1, 2], gap="medium")
            with left_col:
                st.markdown("**INPUT CHAT**")
                st.caption(f"chat_hash: {event['chat_hash']}")
                st.code(event["chat_text"], language="text")

            with right_col:
                st.markdown("**OUTPUT BATCH TABLE**")
                st.dataframe(
                    event["styled_table"],
                    use_container_width=True,
                    height=260,
                )
                if event["delta_mode"] == "changed":
                    st.markdown(
                        "<div class='delta-note'>Delta highlight: "
                        "<span style='color:#8df0b7;'>green = new row/cell value</span>, "
                        "<span style='color:#ffd887;'>yellow = modified value vs previous step</span>.</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Baseline step: tabel ditampilkan tanpa highlight delta.")

            st.markdown("---")

    revision_count = sum(1 for e in events if e["step_type"] != "NEW ORDER")
    return revision_count


def render_batch_audit_feed(engine_or_conn: Any) -> None:
    _inject_styles()

    if "batch_audit_lineage_limit" not in st.session_state:
        st.session_state["batch_audit_lineage_limit"] = _DEFAULT_LINEAGE_LIMIT

    st.markdown("<div class='audit-title'>AI Audit Trail - Batch Event-Driven Feed</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='audit-subtitle'>"
        "Global feed tanpa search bar. Menampilkan lineage transaksi batch (chat -> multi-row output) "
        "dengan highlight perubahan sel antar-step."
        "</div>",
        unsafe_allow_html=True,
    )

    ctl_col1, ctl_col2, ctl_col3 = st.columns([1.2, 1, 1], gap="small")
    with ctl_col1:
        batch_size = st.selectbox(
            "Lineage per load",
            options=_LINEAGE_BATCH_OPTIONS,
            index=_LINEAGE_BATCH_OPTIONS.index(_DEFAULT_LINEAGE_LIMIT),
            key="batch_audit_batch_size",
        )
    with ctl_col2:
        if st.button("Refresh Feed", use_container_width=True):
            st.session_state["batch_audit_last_refresh"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            st.rerun()
    with ctl_col3:
        if st.button("Load More Lineages", use_container_width=True):
            st.session_state["batch_audit_lineage_limit"] += int(batch_size)
            st.rerun()

    ctl2_col1, ctl2_col2 = st.columns([1, 3], gap="small")
    with ctl2_col1:
        if st.button("Reset Window", use_container_width=True):
            st.session_state["batch_audit_lineage_limit"] = int(batch_size)
            st.rerun()
    with ctl2_col2:
        refreshed_at = st.session_state.get("batch_audit_last_refresh", "-")
        st.caption(f"Last refresh: {refreshed_at}")

    lineage_limit = int(st.session_state["batch_audit_lineage_limit"])

    try:
        seed_df = _prepare_seed_feed(engine_or_conn, lineage_limit=lineage_limit)
    except Exception as exc:
        st.error(f"Gagal membaca feed audit dari database: {exc}")
        return

    if seed_df.empty:
        st.info("Belum ada data pada order_dataset/raw_chats untuk audit feed.")
        return

    feed_df, lineage_meta = _assign_lineage_components(seed_df)
    if feed_df.empty or lineage_meta.empty:
        st.info("Tidak ada lineage yang dapat dibangun dari data saat ini.")
        return

    lineage_meta = lineage_meta.sort_values(
        by=["latest_activity_at", "lineage_id"],
        ascending=[False, True],
        kind="stable",
    ).reset_index(drop=True)
    selected_meta = lineage_meta.head(lineage_limit).copy()
    selected_ids = selected_meta["lineage_id"].tolist()
    selected_feed = feed_df[feed_df["lineage_id"].isin(selected_ids)].copy()

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Lineages Loaded", int(selected_meta.shape[0]))
    kpi2.metric("Order Rows Loaded", int(selected_feed.shape[0]))
    kpi3.metric(
        "Distinct Chat Events",
        int(selected_feed["raw_chat_id"].astype(str).str.strip().replace("", pd.NA).dropna().nunique()),
    )

    st.markdown(
        "<span class='audit-chip'>Event-driven batch feed</span>"
        "<span class='audit-chip'>Chronological inside each lineage</span>"
        f"<span class='audit-chip'>Current window: {lineage_limit} lineages</span>",
        unsafe_allow_html=True,
    )

    total_revision_steps = 0
    feed_placeholder = st.empty()
    with feed_placeholder.container():
        for _, row in selected_meta.iterrows():
            lineage_id = _to_text(row["lineage_id"])
            lineage_rows = selected_feed[selected_feed["lineage_id"] == lineage_id].copy()
            total_revision_steps += _render_lineage_block(
                lineage_id=lineage_id,
                lineage_df=lineage_rows,
                latest_activity=row["latest_activity_at"],
            )

    st.caption(
        f"Rendered {int(selected_meta.shape[0])} lineage blocks from latest activity window. "
        f"Revision/Merge steps detected: {total_revision_steps}."
    )


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
