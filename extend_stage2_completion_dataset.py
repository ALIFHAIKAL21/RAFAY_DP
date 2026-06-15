from __future__ import annotations

import json
import random
import re
from collections import Counter
from dataclasses import replace
from pathlib import Path

from generate_stage2_completion_dataset import (
    OUTPUT_PATH,
    OrderState,
    UnitData,
    clean,
    extract_seed_values,
    random_unit,
    read_source_text,
    render_incoming_message,
    render_state,
    seed_orders,
)


FINAL_TARGET_ROWS = 15000
APPEND_RANDOM_SEED = 20260604

APPEND_PLAN = {
    "match_no_header_noise": 1600,
    "match_fill_slot_multi_qty": 1300,
    "match_full_resend_empty_tail": 900,
    "match_duplicate_resend": 700,
    "match_multi_line_exact": 700,
    "match_header_typo_noise": 800,
    "negative_wrong_route_hard": 1400,
    "negative_wrong_date_hard": 1200,
    "negative_wrong_location_hard": 1000,
    "negative_over_target_hard": 1000,
    "negative_wrong_order_line": 700,
    "negative_empty_only": 400,
    "negative_wrong_unit_or_cbm": 300,
}

EXTRA_LOCATIONS = [
    "ARGOPANTES",
    "ARGOPANTES CIKARANG",
    "MEGAHUB",
    "CIKARANG",
    "CIKOKOL",
    "JNE SUB",
    "JNE SRG",
    "JNE SURABAYA",
    "JNE SEMARANG",
    "JNE SOLO",
    "JNE JATIM",
    "JNE JATENG",
    "KBN CAKUNG",
    "BANDARA CGK",
    "GUDANG CGK",
    "GUDANG CIKARANG",
    "SEMARANG",
    "SURABAYA",
    "MEGAHUB CIKARANG",
    "POOL CIKARANG",
    "POOL ARGOPANTES",
    "CIKARANG BARAT",
    "CIKARANG TIMUR",
    "JNE BANDUNG",
    "JNE DENPASAR",
    "JNE PALEMBANG",
]

EXTRA_ROUTES = [
    "CGK - PKU",
    "CGK - SUB",
    "CGK - JATENG",
    "CGK - JATIM",
    "CGK - JATIM TENTATIF",
    "CGK - JATENG TENTATIVE",
    "CGK - MES",
    "CGK - PLM",
    "CGK - PDG",
    "CGK - DPS",
    "CGK - DENPASAR",
    "CGK - MXG",
    "CGK - TKG",
    "CGK - BDO",
    "CGK - JBR",
    "CGK - JOG",
    "CGK - SOC",
    "CGK - SMG",
    "CGK - MLG",
    "CKR - JATENG",
    "CKR - JATIM",
    "CKR-JATENG TENTATIVE",
    "CKR-JBR",
    "CKR-MXG",
    "SUB-CGK",
    "SRG-CGK",
    "SUX-CGK",
    "CGK - Jl.perak surabaya-PT.BM",
]

EXTRA_DATES = [
    "05 FEB 2026",
    "06 FEB 2026",
    "06 FEBUARI 2026",
    "09 FEBRUARI 2026",
    "13 MARET 2026",
    "15 MARET 2026",
    "18 MARET 2026",
    "21 MARET 2026",
    "22 MARET 2026",
    "23 MARET 2026",
    "02 JUNI 2026",
    "05 Feb 26",
    "06 Feb 26",
    "22 Mar 26",
    "22-03-2026",
    "23-03-2026",
    "02/06/2026",
]

NOISE_PREFIXES = [
    "Fyi pak @Nomor tidak dikenal ini update dari pool,",
    "pak ini lanjutannya ya jangan diclose dulu,",
    "noted pak, tambah data sopir lagi,",
    "maaf pak baru masuk info lapangan,",
    "izin info pak buat jadwal malam,",
    "tolong bantu monitor data ini,",
    "data dari admin pool barusan masuk,",
    "pak yg ini saya kirim lagi biar gak ketumpuk chat,",
    "lanjutan dari order tadi pak,",
    "mohon dibantu ya pak unitnya,",
]

NOISE_SUFFIXES = [
    "",
    "yg bawah masih nunggu kabar sopir",
    "sementara itu dulu pak",
    "data tambahan nya pak",
    "jangan diclose dulu",
    "dari pool minta segera diproses",
    "kalau ada update saya kirim lagi",
]

HEADER_VARIANTS = [
    "REQUEST ORDER ULANG ONCALL {date}",
    "REQUEST ORDER ULANG DAN TAMBAHAN ONCALL {date}",
    "REQUER ORDER ULANG DAN TAMBAHAN ON CALL {date}",
    "REQEST ORDER ULANG DAN TAMABAHAN ONCALL {date}",
    "REQUESTT ORDER ULANG DAN TAMBAHAN ONCALL {date}",
    "REQUEST ULANG ORDER ONCALL {date}",
    "Request Ulang Order On Call Tgl {date}",
    "REQUEST ORDER ONCALL {date}",
    "REQEST ORDER ONCALL {date}",
    "",
]

TIME_LABELS = ["Waktu loading", "Waktu lodng", "Waktu loding", "Waktu loadng", "Jam muat", "Jam"]
ROUTE_LABELS = ["Rute/tujuan", "Rute/tuj", "Rute/tujan", "Rute tujuan", "Tujuan"]
DRIVER_LABELS = ["driver", "DRIVERR", "DRVER", "DRIVR", "Nama", "Nama Driver"]
PLATE_LABELS = ["Nopol", "No Pol", "NOPL", "Nopoll", "No Polisi"]
PHONE_LABELS = ["No hp", "NOHP", "No Hpp", "No Tlp", "No Telp"]


def extend_unique(base: list[str], extras: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in [*base, *extras]:
        value = clean(value).strip(" :;.,")
        if not value:
            continue
        key = value.upper()
        if key in seen:
            continue
        seen.add(key)
        result.append(value.upper())
    return result


def build_seed_pool() -> dict[str, list[str]]:
    seeds = extract_seed_values(read_source_text())
    seeds["locations"] = extend_unique(seeds["locations"], EXTRA_LOCATIONS)
    seeds["routes"] = extend_unique(seeds["routes"], EXTRA_ROUTES)
    seeds["dates"] = extend_unique([], EXTRA_DATES)
    seeds["times"] = extend_unique(
        seeds["times"],
        [
            "SEGERA",
            "02:00",
            "02.00 23-03-2026",
            "03:00",
            "03.00",
            "04:00",
            "06:00/ 06-02-26",
            "07:00 07-02-2026",
            "12:00/17-03-2026",
            "14:00",
            "15:00",
            "17:00",
            "18:00",
            "19:00",
            "20:00",
            "21:00",
            "22.00",
            "23:00",
            "00:00",
        ],
    )
    return seeds


def append_row(
    rows: list[dict[str, object]],
    seen: set[tuple[str, str, str]],
    *,
    text_a: str,
    text_b: str,
    label: str,
    pair_kind: str,
    unit_action: str,
    source_id: str,
) -> bool:
    text_a = clean(text_a)
    text_b = clean(text_b)
    label = label.upper()
    key = (text_a, text_b, label)
    if not text_a or not text_b or key in seen:
        return False
    seen.add(key)
    rows.append(
        {
            "pair_id": f"stage2_completion_{len(rows) + 1:04d}",
            "text_a": text_a,
            "text_b": text_b,
            "label": label,
            "pair_kind": pair_kind,
            "unit_action": unit_action,
            "source_id": source_id,
        }
    )
    return True


def different(values: list[str], current: str) -> str:
    candidates = [value for value in values if value.upper() != current.upper()]
    return random.choice(candidates or values)


def make_varied_order(seeds: dict[str, list[str]], index: int, *, complete: bool = False) -> OrderState:
    unit_type, cbm = random.choice([("TWB", 50), ("WB", 50), ("CDDL", 24)])
    qty = random.randint(1, 20)
    complete_count = qty if complete else random.randint(0, max(0, qty - 1))
    route = random.choice(seeds["routes"])
    units = tuple(
        UnitData(
            loading_time=random.choice(seeds["times"]),
            route=route,
            driver=random.choice(seeds["drivers"]).upper(),
            plate=random.choice(seeds["plates"]).upper(),
            phone=random.choice(seeds["phones"]),
        )
        for _ in range(complete_count)
    )
    empty_count = max(0, qty - complete_count)
    return OrderState(
        source_id=f"stage2_ext_order_{index:05d}",
        request_date=random.choice(seeds["dates"]),
        qty_target=qty,
        unit_type=unit_type,
        cbm=cbm,
        location=random.choice(seeds["locations"]),
        route=route,
        existing_units=units,
        empty_times=tuple(random.choice(seeds["times"]) for _ in range(empty_count)),
    )


def complete_version(order: OrderState, seeds: dict[str, list[str]]) -> OrderState:
    missing = max(0, order.qty_target - order.complete_count)
    new_units = tuple(
        random_unit(seeds, order, loading_time=random.choice(order.empty_times or seeds["times"]))
        for _ in range(missing)
    )
    return replace(order, existing_units=tuple(order.existing_units + new_units)[: order.qty_target], empty_times=())


def wrong_version(order: OrderState, seeds: dict[str, list[str]], field: str) -> OrderState:
    if field == "route":
        return replace(order, route=different(seeds["routes"], order.route))
    if field == "location":
        return replace(order, location=different(seeds["locations"], order.location))
    if field == "date":
        return replace(order, request_date=different(seeds["dates"], order.request_date))
    if field == "unit":
        return replace(order, unit_type="CDDL" if order.unit_type != "CDDL" else "TWB", cbm=24 if order.unit_type != "CDDL" else 50)
    if field == "cbm":
        return replace(order, cbm=24 if order.cbm != 24 else 50)
    raise ValueError(field)


def make_units(seeds: dict[str, list[str]], order: OrderState, min_count: int = 1, max_count: int = 5) -> list[UnitData]:
    remaining = max(1, order.remaining_slots)
    count = random.randint(min_count, min(max_count, remaining))
    return [
        random_unit(seeds, order, loading_time=random.choice(order.empty_times or seeds["times"]))
        for _ in range(count)
    ]


def render_fieldless(order: OrderState, units: list[UnitData], *, header: bool) -> str:
    chunks = []
    if random.random() < 0.75:
        chunks.append(random.choice(NOISE_PREFIXES))
    if header:
        template = random.choice(HEADER_VARIANTS)
        if template:
            chunks.append(template.format(date=order.request_date))
    if random.random() < 0.85:
        chunks.append(f"{order.qty_target} unit {order.unit_type} {order.cbm} cbm")
    if random.random() < 0.85:
        chunks.append(f"lokasi {order.location}")
    for unit in units:
        chunks.append(
            " ".join(
                [
                    f"jam {unit.loading_time}",
                    f"tujuan {unit.route}",
                    f"nama {unit.driver}",
                    f"no pol {unit.plate}",
                    f"no tlp {unit.phone}",
                ]
            )
        )
    suffix = random.choice(NOISE_SUFFIXES)
    if suffix:
        chunks.append(suffix)
    return clean(" ".join(chunks))


def render_noisy(order: OrderState, units: list[UnitData], *, header: bool, meta: bool, fieldless: bool = False) -> str:
    if fieldless:
        return render_fieldless(order, units, header=header)
    prefix = random.choice(NOISE_PREFIXES) if random.random() < 0.45 else ""
    body = render_incoming_message(
        order,
        units,
        random.randint(0, 100000),
        include_header=header,
        include_order_meta=meta,
        include_empty=all(not u.driver and not u.plate and not u.phone for u in units),
    )
    suffix = random.choice(NOISE_SUFFIXES) if random.random() < 0.35 else ""
    return clean(" ".join([prefix, body, suffix]))


def render_empty_only(order: OrderState) -> str:
    header = random.choice(HEADER_VARIANTS).format(date=order.request_date)
    blocks = []
    for _ in range(random.randint(1, min(5, max(1, order.remaining_slots)))):
        blocks.append(
            "\n".join(
                [
                    f"{random.choice(TIME_LABELS)} : {random.choice(order.empty_times or ('SEGERA',))}",
                    f"{random.choice(ROUTE_LABELS)} : {order.route}",
                    f"{random.choice(DRIVER_LABELS)} :",
                    f"{random.choice(PLATE_LABELS)} :",
                    f"{random.choice(PHONE_LABELS)} :",
                ]
            )
        )
    return clean("\n".join([random.choice(NOISE_PREFIXES), header, f"{order.qty_target} UNIT {order.unit_type} {order.cbm} CBM", f"Lokasi : {order.location}", *blocks]))


def base_orders(seeds: dict[str, list[str]]) -> list[OrderState]:
    explicit = seed_orders()
    synthetic = [make_varied_order(seeds, i) for i in range(500)]
    complete = [make_varied_order(seeds, i + 500, complete=True) for i in range(120)]
    return [*explicit, *synthetic, *complete]


def add_category(
    rows: list[dict[str, object]],
    seen: set[tuple[str, str, str]],
    seeds: dict[str, list[str]],
    orders: list[OrderState],
    category: str,
) -> bool:
    order = random.choice(orders)
    if category == "match_no_header_noise":
        units = make_units(seeds, order, 1, 4)
        return append_row(
            rows,
            seen,
            text_a=render_state(order, random.randint(0, 99)),
            text_b=render_noisy(order, units, header=False, meta=random.random() < 0.6, fieldless=True),
            label="MATCH",
            pair_kind=category,
            unit_action="NEW_FILL_SLOT",
            source_id=order.source_id,
        )

    if category == "match_fill_slot_multi_qty":
        units = make_units(seeds, order, 1, 6)
        return append_row(
            rows,
            seen,
            text_a=render_state(order, random.randint(0, 99)),
            text_b=render_noisy(order, units, header=True, meta=True, fieldless=random.random() < 0.25),
            label="MATCH",
            pair_kind=category,
            unit_action="NEW_FILL_SLOT",
            source_id=order.source_id,
        )

    if category == "match_full_resend_empty_tail":
        units = list(order.existing_units[: random.randint(0, min(3, len(order.existing_units)))])
        units += make_units(seeds, order, 1, 4)
        empty_tail = [
            UnitData(random.choice(order.empty_times or seeds["times"]), order.route, "", "", "")
            for _ in range(random.randint(0, 3))
        ]
        return append_row(
            rows,
            seen,
            text_a=render_state(order, random.randint(0, 99)),
            text_b=render_noisy(order, units + empty_tail, header=True, meta=True, fieldless=False),
            label="MATCH",
            pair_kind=category,
            unit_action="RESEND_WITH_NEW_FILL",
            source_id=order.source_id,
        )

    if category == "match_duplicate_resend":
        if not order.existing_units:
            return False
        units = random.sample(list(order.existing_units), k=random.randint(1, min(4, len(order.existing_units))))
        return append_row(
            rows,
            seen,
            text_a=render_state(order, random.randint(0, 99)),
            text_b=render_noisy(order, units, header=random.random() < 0.8, meta=random.random() < 0.8, fieldless=random.random() < 0.25),
            label="MATCH",
            pair_kind=category,
            unit_action="DUPLICATE_EXISTING_UNIT",
            source_id=order.source_id,
        )

    if category == "match_multi_line_exact":
        route = random.choice(["CGK - JATENG", "CGK - JATIM", "CGK - PKU", "CGK - SUB", "CGK - MES"])
        line = replace(order, qty_target=1, unit_type="CDDL", cbm=24, location=random.choice(["MEGAHUB", "CIKARANG", "ARGOPANTES"]), route=route, existing_units=(), empty_times=("23:00",))
        unit = random_unit(seeds, line, loading_time="23:00")
        return append_row(
            rows,
            seen,
            text_a=render_state(line, random.randint(0, 99)),
            text_b=render_noisy(line, [unit], header=random.random() < 0.7, meta=True, fieldless=random.random() < 0.35),
            label="MATCH",
            pair_kind=category,
            unit_action="NEW_FILL_SLOT",
            source_id=line.source_id,
        )

    if category == "match_header_typo_noise":
        units = make_units(seeds, order, 1, 3)
        return append_row(
            rows,
            seen,
            text_a=render_state(order, random.randint(0, 99)),
            text_b=render_noisy(order, units, header=True, meta=random.random() < 0.85, fieldless=random.random() < 0.2),
            label="MATCH",
            pair_kind=category,
            unit_action="NEW_FILL_SLOT",
            source_id=order.source_id,
        )

    if category == "negative_wrong_route_hard":
        incoming = wrong_version(order, seeds, "route")
        units = make_units(seeds, incoming, 1, 4)
        return append_row(
            rows,
            seen,
            text_a=render_state(order, random.randint(0, 99)),
            text_b=render_noisy(incoming, units, header=random.random() < 0.8, meta=True, fieldless=random.random() < 0.25),
            label="NO_MATCH",
            pair_kind=category,
            unit_action="DIFFERENT_ORDER",
            source_id=order.source_id,
        )

    if category == "negative_wrong_date_hard":
        incoming = wrong_version(order, seeds, "date")
        units = make_units(seeds, incoming, 1, 4)
        return append_row(
            rows,
            seen,
            text_a=render_state(order, random.randint(0, 99)),
            text_b=render_noisy(incoming, units, header=True, meta=True, fieldless=random.random() < 0.25),
            label="NO_MATCH",
            pair_kind=category,
            unit_action="DIFFERENT_ORDER",
            source_id=order.source_id,
        )

    if category == "negative_wrong_location_hard":
        incoming = wrong_version(order, seeds, "location")
        units = make_units(seeds, incoming, 1, 4)
        return append_row(
            rows,
            seen,
            text_a=render_state(order, random.randint(0, 99)),
            text_b=render_noisy(incoming, units, header=random.random() < 0.8, meta=True, fieldless=random.random() < 0.3),
            label="NO_MATCH",
            pair_kind=category,
            unit_action="DIFFERENT_ORDER",
            source_id=order.source_id,
        )

    if category == "negative_over_target_hard":
        complete_order = complete_version(order, seeds)
        unit = random_unit(seeds, complete_order)
        return append_row(
            rows,
            seen,
            text_a=render_state(complete_order, random.randint(0, 99)),
            text_b=render_noisy(complete_order, [unit], header=random.random() < 0.85, meta=True, fieldless=random.random() < 0.3),
            label="NO_MATCH",
            pair_kind=category,
            unit_action="OVER_TARGET_QTY",
            source_id=complete_order.source_id,
        )

    if category == "negative_wrong_order_line":
        route_a, route_b = random.sample(["CGK - JATENG", "CGK - JATIM", "CGK - PKU", "CGK - SUB", "CGK - MES", "CGK - PLM"], 2)
        line_a = replace(order, qty_target=1, unit_type="CDDL", cbm=24, location=random.choice(["MEGAHUB", "CIKARANG", "ARGOPANTES"]), route=route_a, existing_units=(), empty_times=("23:00",))
        line_b = replace(line_a, route=route_b)
        unit = random_unit(seeds, line_b, loading_time="23:00")
        return append_row(
            rows,
            seen,
            text_a=render_state(line_a, random.randint(0, 99)),
            text_b=render_noisy(line_b, [unit], header=random.random() < 0.8, meta=True, fieldless=random.random() < 0.35),
            label="NO_MATCH",
            pair_kind=category,
            unit_action="DIFFERENT_ORDER_LINE",
            source_id=line_a.source_id,
        )

    if category == "negative_empty_only":
        return append_row(
            rows,
            seen,
            text_a=render_state(order, random.randint(0, 99)),
            text_b=render_empty_only(order),
            label="NO_MATCH",
            pair_kind=category,
            unit_action="EMPTY_SLOT",
            source_id=order.source_id,
        )

    if category == "negative_wrong_unit_or_cbm":
        incoming = wrong_version(order, seeds, random.choice(["unit", "cbm"]))
        units = make_units(seeds, incoming, 1, 4)
        return append_row(
            rows,
            seen,
            text_a=render_state(order, random.randint(0, 99)),
            text_b=render_noisy(incoming, units, header=random.random() < 0.8, meta=True, fieldless=random.random() < 0.2),
            label="NO_MATCH",
            pair_kind=category,
            unit_action="DIFFERENT_ORDER",
            source_id=order.source_id,
        )

    raise ValueError(category)


def load_rows() -> list[dict[str, object]]:
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(f"Dataset tidak ditemukan: {OUTPUT_PATH}")
    rows = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("Dataset harus berupa JSON array.")
    return rows


def validate(rows: list[dict[str, object]], original_count: int) -> None:
    if len(rows) != FINAL_TARGET_ROWS:
        raise ValueError(f"Expected {FINAL_TARGET_ROWS} rows, got {len(rows)}")
    labels = Counter(row["label"] for row in rows)
    expected_each = FINAL_TARGET_ROWS // 2
    if labels["MATCH"] != expected_each or labels["NO_MATCH"] != expected_each:
        raise ValueError(f"Label tidak seimbang: {dict(labels)}")
    if rows[original_count - 1]["pair_id"] != f"stage2_completion_{original_count:04d}":
        raise ValueError("Urutan dataset lama berubah.")
    for idx, row in enumerate(rows):
        if row.get("label") not in {"MATCH", "NO_MATCH"}:
            raise ValueError(f"Label invalid di row {idx}: {row.get('label')}")
        if not clean(row.get("text_a", "")) or not clean(row.get("text_b", "")):
            raise ValueError(f"text_a/text_b kosong di row {idx}")


def main() -> None:
    random.seed(APPEND_RANDOM_SEED)
    rows = load_rows()
    original_count = len(rows)
    if original_count >= FINAL_TARGET_ROWS:
        print(f"Dataset sudah >= target: {original_count} row")
        return

    seen = {(clean(r["text_a"]), clean(r["text_b"]), str(r["label"]).upper()) for r in rows}
    seeds = build_seed_pool()
    orders = base_orders(seeds)

    before_counts = Counter(row["label"] for row in rows)
    target_each = FINAL_TARGET_ROWS // 2
    needed = {
        "MATCH": target_each - before_counts["MATCH"],
        "NO_MATCH": target_each - before_counts["NO_MATCH"],
    }
    if needed["MATCH"] < 0 or needed["NO_MATCH"] < 0:
        raise ValueError(f"Dataset awal sudah tidak seimbang untuk target {FINAL_TARGET_ROWS}: {dict(before_counts)}")

    appended_by_kind: Counter[str] = Counter()
    for category, requested_count in APPEND_PLAN.items():
        label = "MATCH" if category.startswith("match_") else "NO_MATCH"
        count = min(requested_count, needed[label])
        attempts = 0
        while appended_by_kind[category] < count:
            attempts += 1
            if attempts > count * 120:
                raise RuntimeError(f"Gagal memenuhi kategori {category}: {appended_by_kind[category]}/{count}")
            if add_category(rows, seen, seeds, orders, category):
                appended_by_kind[category] += 1
                needed[label] -= 1

    while len(rows) < FINAL_TARGET_ROWS:
        label = "MATCH" if needed["MATCH"] > 0 else "NO_MATCH"
        categories = [k for k in APPEND_PLAN if (k.startswith("match_") if label == "MATCH" else k.startswith("negative_"))]
        category = random.choice(categories)
        if add_category(rows, seen, seeds, orders, category):
            appended_by_kind[category] += 1
            needed[label] -= 1

    validate(rows, original_count)
    OUTPUT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    label_counts = Counter(row["label"] for row in rows)
    action_counts = Counter(row["unit_action"] for row in rows)
    print(f"Output: {OUTPUT_PATH}")
    print(f"Rows before: {original_count}")
    print(f"Rows after : {len(rows)}")
    print(f"Label distribution: {dict(label_counts)}")
    print(f"Appended by kind: {dict(appended_by_kind)}")
    print(f"Unit actions: {dict(action_counts)}")


if __name__ == "__main__":
    main()
