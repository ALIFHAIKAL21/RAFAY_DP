from __future__ import annotations

import json
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT_DIR / "data" / "chat" / "processed" / "SPC" / "stage2_completion_matcher_dataset.json"
TARGET_ROWS = 3000
RANDOM_SEED = 42


@dataclass(frozen=True)
class UnitData:
    loading_time: str
    route: str
    driver: str = ""
    plate: str = ""
    phone: str = ""


@dataclass(frozen=True)
class OrderState:
    source_id: str
    request_date: str
    qty_target: int
    unit_type: str
    cbm: int
    location: str
    route: str
    existing_units: tuple[UnitData, ...]
    empty_times: tuple[str, ...]

    @property
    def complete_count(self) -> int:
        return len(
            [
                unit
                for unit in self.existing_units
                if unit.driver.strip() and unit.plate.strip() and unit.phone.strip()
            ]
        )

    @property
    def remaining_slots(self) -> int:
        return max(0, self.qty_target - self.complete_count)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def read_source_text() -> str:
    paths = [
        ROOT_DIR / "test_case" / "got.txt",
        *sorted((ROOT_DIR / "test_case" / "pesanan_baru").glob("*.txt")),
        *sorted((ROOT_DIR / "test_case" / "pesanan_susulan" / "pelengkapan").glob("*.txt")),
    ]
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths if path.exists())


def unique_values(values: list[str], fallback: list[str], limit: int = 80) -> list[str]:
    seen = set()
    result: list[str] = []
    for value in [*values, *fallback]:
        value = clean(value).strip(" :;.,")
        if not value:
            continue
        key = value.upper()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
        if len(result) >= limit:
            break
    return result


def extract_seed_values(source_text: str) -> dict[str, list[str]]:
    driver_pattern = re.compile(
        r"(?im)^\s*(?:driver\s*\d*|driverr|drver|drivr|nama)\s*:?\s*([^\r\n]+)"
    )
    plate_pattern = re.compile(
        r"(?im)^\s*(?:nopol|nopoll|nopl|no\s*pol)\s*:?\s*([A-Z]{1,2}\s*\d{3,5}\s*[A-Z]{1,3})"
    )
    phone_pattern = re.compile(
        r"(?im)^\s*(?:no\s*hp|nohp|no\s*hpp|no\s*tlp|no\s*tlp|no\s*telp)\s*:?\s*([+0-9][+\d\s/-]{5,})"
    )
    location_pattern = re.compile(r"(?im)^\s*(?:lokasi|loksai|pickup)\s*:?\s*([^\r\n]+)")
    route_pattern = re.compile(r"(?im)^\s*(?:rute\s*/?\s*(?:tujuan|tuj|tujan)|tujuan)\s*:?\s*([^\r\n]+)")
    time_pattern = re.compile(r"(?im)^\s*(?:waktu\s*l(?:oa)?d(?:i)?ng|jam\s*muat|waktu)\s*:?\s*([^\r\n]+)")

    drivers = [
        value
        for value in driver_pattern.findall(source_text)
        if value.strip() and not re.search(r"(?i)nopol|no hp|rafay|pak\b", value)
    ]
    return {
        "drivers": unique_values(
            drivers,
            [
                "IWAN",
                "MARTIN",
                "RANDI",
                "AHMAD",
                "JUNAM",
                "AGUNG",
                "ADRI",
                "DANDI",
                "AJENG",
                "ANDI",
                "RANDO",
                "AGUS / DIAN",
                "LATIF",
                "HANIF",
            ],
        ),
        "plates": unique_values(
            plate_pattern.findall(source_text),
            [
                "B 9702 TX",
                "B 9357 FXR",
                "B 9702 XX",
                "B 9357 TT",
                "B 9357 ARG",
                "BM 8496 AU",
                "BM 8496 AA",
                "BM 8496 ZZ",
                "BM 8496 ZX",
                "BM 8496 AR",
                "AD 8857 DV",
                "B 555 AX",
            ],
        ),
        "phones": unique_values(
            phone_pattern.findall(source_text),
            [
                "087844620137",
                "81382430619",
                "0878446223834",
                "81382428374",
                "81382422849",
                "085364721905",
                "085364721908",
                "0853647219918",
                "085364721993",
                "0853647229304",
                "+62 815-5952-1259",
                "081574673448",
            ],
        ),
        "locations": unique_values(
            location_pattern.findall(source_text),
            ["ARGOPANTES", "MEGAHUB", "CIKARANG", "CIKOKOL", "JNE SUB", "JNE SRG", "SEMARANG"],
        ),
        "routes": unique_values(
            route_pattern.findall(source_text),
            [
                "CGK - PKU",
                "CGK - SUB",
                "CGK - JATENG",
                "CGK - JATIM",
                "CGK - JATIM TENTATIF",
                "CGK - MES",
                "SUB-CGK",
                "SRG-CGK",
            ],
        ),
        "times": unique_values(
            time_pattern.findall(source_text),
            ["SEGERA", "15:00", "18:00", "14:00", "17:00", "19:00", "20:00", "23:00", "02.00 23-03-2026"],
        ),
    }


def seed_orders() -> list[OrderState]:
    return [
        OrderState(
            source_id="case1_incremental_shortage",
            request_date="22 MARET 2026",
            qty_target=5,
            unit_type="TWB",
            cbm=50,
            location="ARGOPANTES",
            route="CGK - PKU",
            existing_units=(
                UnitData("02.00 23-03-2026", "CGK - PKU", "SUTRISNO", "BM 8496 AU", "085364721905"),
            ),
            empty_times=("03.00", "04.00", "02.00 23-03-2026", "03.00"),
        ),
        OrderState(
            source_id="case2_two_existing_then_three",
            request_date="22 MARET 2026",
            qty_target=5,
            unit_type="TWB",
            cbm=50,
            location="ARGOPANTES",
            route="CGK - PKU",
            existing_units=(
                UnitData("15:00", "CGK - PKU", "IWAN", "B 9702 TX", "087844620137"),
                UnitData("18:00", "CGK - PKU", "MARTIN", "B 9357 FXR", "81382430619"),
            ),
            empty_times=("15:00", "14:00", "14:00"),
        ),
        OrderState(
            source_id="case3_explicit_empty_slots",
            request_date="22 MARET 2026",
            qty_target=5,
            unit_type="TWB",
            cbm=50,
            location="ARGOPANTES",
            route="CGK - PKU",
            existing_units=(
                UnitData("15:00", "CGK - PKU", "IWAN", "B 9702 TX", "087844620137"),
            ),
            empty_times=("18:00", "17:00", "19:00", "20:00"),
        ),
        OrderState(
            source_id="case4_megahub_jateng_line",
            request_date="02 JUNI 2026",
            qty_target=1,
            unit_type="CDDL",
            cbm=24,
            location="MEGAHUB",
            route="CGK - JATENG",
            existing_units=(),
            empty_times=("23:00",),
        ),
        OrderState(
            source_id="case4_megahub_jatim_line",
            request_date="02 JUNI 2026",
            qty_target=1,
            unit_type="CDDL",
            cbm=24,
            location="MEGAHUB",
            route="CGK - JATIM",
            existing_units=(),
            empty_times=("23:00",),
        ),
        OrderState(
            source_id="case5_full_resend_three_existing",
            request_date="06 FEB 2026",
            qty_target=5,
            unit_type="CDDL",
            cbm=24,
            location="ARGOPANTES",
            route="CGK - JATIM TENTATIF",
            existing_units=(
                UnitData("SEGERA", "CGK - JATIM TENTATIF", "ADIP", "B 3309 AU", "+62 852-4568-1444"),
                UnitData("SEGERA", "CGK - JATIM TENTATIF", "DERI SUHENDAR", "L 6754 BB", "+62 852-8278-1280"),
                UnitData("SEGERA", "CGK - JATIM TENTATIF", "RANDY", "L 7823 AA", "+62 852-8278-8271"),
            ),
            empty_times=("SEGERA", "SEGERA"),
        ),
        OrderState(
            source_id="case6_got_empty_slots",
            request_date="06 FEBUARI 2026",
            qty_target=5,
            unit_type="TWB",
            cbm=50,
            location="ARGOPANTES",
            route="CGK - SUB",
            existing_units=(
                UnitData("SEGERA", "CGK - SUB", "HENDRA S.P", "D 9044 AG", "+62 877-8667-6177"),
            ),
            empty_times=("18:00", "21:00", "00:00", "03:00 06/02/2026"),
        ),
    ]


HEADER_VARIANTS = [
    "REQUEST ORDER ULANG ONCALL {date}",
    "REQUEST ORDER ULANG DAN TAMBAHAN ONCALL {date}",
    "REQUER ORDER ULANG DAN TAMBAHAN ON CALL {date}",
    "REQUESTT ORDER ULANG DAN TAMBAHAN ONCALL {date}",
    "REQUEST ORDER ONCALL {date}",
    "Request Unit On Call Tgl {date}",
    "ini lanjutannya ya pak {date}",
    "data tambahan dari pool {date}",
    "",
]

STATE_TEMPLATES = [
    (
        "ORDER_STATE | Tanggal request: {date} | Qty target: {qty} | Terisi: {complete}/{qty} | "
        "Sisa slot: {remaining} | Unit: {unit_type} {cbm} CBM | Lokasi: {location} | "
        "Rute/tujuan: {route} | Unit terdata: {existing}"
    ),
    (
        "DB_ORDER_AKTIF | RO={date}; target={qty}; complete={complete}; empty={remaining}; "
        "truck={unit_type}/{cbm} cbm; pickup={location}; route={route}; existing_driver={existing}"
    ),
    (
        "Kandidat pesanan belum lengkap: {date}, {qty} UNIT {unit_type} {cbm} Cbm, "
        "lokasi {location}, tujuan {route}, sudah lengkap {complete} dari {qty}. Riwayat: {existing}"
    ),
    (
        "STATE SLOT PELENGKAPAN | tanggal {date} | lokasi {location} | rute {route} | "
        "tipe {unit_type} {cbm} | target qty {qty} | terisi {complete} | kosong {remaining} | {existing}"
    ),
]

FIELD_LABELS = {
    "location": ["Lokasi", "Loksai", "Pickup"],
    "time": ["Waktu loading", "Waktu lodng", "Waktu loding", "Jam muat"],
    "route": ["Rute/tujuan", "Rute/tuj", "Rute/tujan", "Tujuan"],
    "driver": ["driver", "DRIVERR", "DRVER", "Nama", "DRIVR"],
    "plate": ["Nopol", "No Pol", "NOPL", "Nopoll"],
    "phone": ["No hp", "NOHP", "No Hpp", "No Tlp"],
}


def random_unit(seeds: dict[str, list[str]], order: OrderState, loading_time: str | None = None) -> UnitData:
    return UnitData(
        loading_time=loading_time or random.choice(seeds["times"]),
        route=order.route,
        driver=random.choice(seeds["drivers"]).upper(),
        plate=random.choice(seeds["plates"]).upper(),
        phone=random.choice(seeds["phones"]),
    )


def existing_summary(order: OrderState) -> str:
    if not order.existing_units:
        return "belum ada driver/nopol/no hp"
    parts = []
    for unit in order.existing_units[:4]:
        parts.append(f"{unit.loading_time} {unit.driver} {unit.plate} {unit.phone}")
    return "; ".join(parts)


def render_state(order: OrderState, template_index: int) -> str:
    return clean(
        STATE_TEMPLATES[template_index % len(STATE_TEMPLATES)].format(
            date=order.request_date,
            qty=order.qty_target,
            complete=order.complete_count,
            remaining=order.remaining_slots,
            unit_type=order.unit_type,
            cbm=order.cbm,
            location=order.location,
            route=order.route,
            existing=existing_summary(order),
        )
    )


def header_for(order: OrderState, variant_index: int) -> str:
    template = HEADER_VARIANTS[variant_index % len(HEADER_VARIANTS)]
    return template.format(date=order.request_date).strip()


def pick_label(field_name: str, variant_index: int) -> str:
    labels = FIELD_LABELS[field_name]
    return labels[variant_index % len(labels)]


def render_units_block(units: list[UnitData], variant_index: int, include_empty: bool = False) -> str:
    blocks: list[str] = []
    for unit_index, unit in enumerate(units):
        idx = variant_index + unit_index
        driver = unit.driver if unit.driver or not include_empty else ""
        plate = unit.plate if unit.plate or not include_empty else ""
        phone = unit.phone if unit.phone or not include_empty else ""
        blocks.append(
            "\n".join(
                [
                    f"{pick_label('time', idx)} : {unit.loading_time}",
                    f"{pick_label('route', idx)} : {unit.route}",
                    f"{pick_label('driver', idx)} : {driver}",
                    f"{pick_label('plate', idx)} : {plate}",
                    f"{pick_label('phone', idx)} : {phone}",
                ]
            )
        )
    return "\n\n".join(blocks)


def render_incoming_message(
    order: OrderState,
    units: list[UnitData],
    variant_index: int,
    *,
    include_header: bool = True,
    include_order_meta: bool = True,
    include_empty: bool = False,
) -> str:
    lines: list[str] = []
    if include_header:
        header = header_for(order, variant_index)
        if header:
            lines.append(header)
    if include_order_meta:
        unit_separator = "/" if variant_index % 2 else " "
        lines.extend(
            [
                f"{order.qty_target} UNIT {order.unit_type}{unit_separator}{order.cbm} CBM",
                f"{pick_label('location', variant_index)} : {order.location}",
            ]
        )
    lines.append(render_units_block(units, variant_index, include_empty=include_empty))
    return clean("\n".join(lines))


def mutate_order(order: OrderState, seeds: dict[str, list[str]], mutation: str) -> OrderState:
    def different(values: list[str], current: str) -> str:
        candidates = [value for value in values if value.upper() != current.upper()]
        return random.choice(candidates or values)

    if mutation == "route":
        return OrderState(
            **{**order.__dict__, "route": different(seeds["routes"], order.route)}
        )
    if mutation == "location":
        return OrderState(
            **{**order.__dict__, "location": different(seeds["locations"], order.location)}
        )
    if mutation == "date":
        dates = ["21 MARET 2026", "23 MARET 2026", "06 FEB 2026", "02 JUNI 2026", "13 MARET 2026"]
        return OrderState(**{**order.__dict__, "request_date": different(dates, order.request_date)})
    if mutation == "unit_type":
        if order.unit_type.upper() == "TWB":
            return OrderState(**{**order.__dict__, "unit_type": "CDDL", "cbm": 24})
        return OrderState(**{**order.__dict__, "unit_type": "TWB", "cbm": 50})
    if mutation == "cbm":
        return OrderState(**{**order.__dict__, "cbm": 24 if order.cbm != 24 else 50})
    raise ValueError(f"Unknown mutation: {mutation}")


def add_pair(
    rows: list[dict[str, object]],
    seen: set[tuple[str, str, str]],
    *,
    order: OrderState,
    incoming_order: OrderState,
    units: list[UnitData],
    label: str,
    pair_kind: str,
    action: str,
    variant_index: int,
    include_header: bool = True,
    include_order_meta: bool = True,
    include_empty: bool = False,
) -> None:
    text_a = render_state(order, variant_index)
    text_b = render_incoming_message(
        incoming_order,
        units,
        variant_index,
        include_header=include_header,
        include_order_meta=include_order_meta,
        include_empty=include_empty,
    )
    label = label.upper()
    key = (text_a, text_b, label)
    if key in seen:
        return
    seen.add(key)
    rows.append(
        {
            "pair_id": f"stage2_completion_{len(rows) + 1:04d}",
            "text_a": text_a,
            "text_b": text_b,
            "label": label,
            "pair_kind": pair_kind,
            "unit_action": action,
            "source_id": order.source_id,
        }
    )


def make_random_order(seeds: dict[str, list[str]], index: int) -> OrderState:
    unit_type, cbm = random.choice([("TWB", 50), ("WB", 50), ("CDDL", 24)])
    qty = random.choice([1, 2, 3, 4, 5, 6, 10])
    complete = random.randint(0, max(0, qty - 1))
    route = random.choice(seeds["routes"]).upper()
    units = tuple(
        UnitData(
            loading_time=random.choice(seeds["times"]).upper(),
            route=route,
            driver=random.choice(seeds["drivers"]).upper(),
            plate=random.choice(seeds["plates"]).upper(),
            phone=random.choice(seeds["phones"]),
        )
        for _ in range(complete)
    )
    empty_count = max(1, qty - complete)
    return OrderState(
        source_id=f"synthetic_order_{index:03d}",
        request_date=random.choice(["05 FEB 2026", "06 FEBUARI 2026", "13 MARET 2026", "22 MARET 2026", "02 JUNI 2026"]),
        qty_target=qty,
        unit_type=unit_type,
        cbm=cbm,
        location=random.choice(seeds["locations"]).upper(),
        route=route,
        existing_units=units,
        empty_times=tuple(random.choice(seeds["times"]).upper() for _ in range(empty_count)),
    )


def add_explicit_case_pairs(rows: list[dict[str, object]], seen: set[tuple[str, str, str]], seeds: dict[str, list[str]]) -> None:
    orders = seed_orders()
    for idx, order in enumerate(orders):
        fill_units = [
            random_unit(seeds, order, loading_time=time)
            for time in order.empty_times[: max(1, min(3, order.remaining_slots))]
        ]
        add_pair(
            rows,
            seen,
            order=order,
            incoming_order=order,
            units=fill_units,
            label="MATCH",
            pair_kind="positive_fill_shortage",
            action="NEW_FILL_SLOT",
            variant_index=idx,
        )
        add_pair(
            rows,
            seen,
            order=order,
            incoming_order=order,
            units=fill_units[:1],
            label="MATCH",
            pair_kind="positive_without_followup_header",
            action="NEW_FILL_SLOT",
            variant_index=idx + 11,
            include_header=False,
            include_order_meta=True,
        )
        if order.existing_units:
            add_pair(
                rows,
                seen,
                order=order,
                incoming_order=order,
                units=[order.existing_units[0]],
                label="MATCH",
                pair_kind="positive_duplicate_resend",
                action="DUPLICATE_EXISTING_UNIT",
                variant_index=idx + 21,
                include_header=True,
                include_order_meta=True,
            )
            resend_units = [*order.existing_units[:2], *fill_units[:2]]
            add_pair(
                rows,
                seen,
                order=order,
                incoming_order=order,
                units=resend_units,
                label="MATCH",
                pair_kind="positive_full_or_partial_resend",
                action="RESEND_WITH_NEW_FILL",
                variant_index=idx + 31,
                include_header=True,
                include_order_meta=True,
            )

        for mutation_index, mutation in enumerate(["route", "location", "date", "unit_type", "cbm"]):
            wrong_order = mutate_order(order, seeds, mutation)
            wrong_unit = random_unit(seeds, wrong_order, loading_time=random.choice(order.empty_times or seeds["times"]))
            add_pair(
                rows,
                seen,
                order=order,
                incoming_order=wrong_order,
                units=[wrong_unit],
                label="NO_MATCH",
                pair_kind=f"negative_wrong_{mutation}",
                action="DIFFERENT_ORDER",
                variant_index=idx + mutation_index + 41,
            )

        empty_unit = UnitData(
            loading_time=random.choice(order.empty_times or seeds["times"]),
            route=order.route,
            driver="",
            plate="",
            phone="",
        )
        add_pair(
            rows,
            seen,
            order=order,
            incoming_order=order,
            units=[empty_unit],
            label="NO_MATCH",
            pair_kind="negative_empty_incoming_unit",
            action="EMPTY_SLOT",
            variant_index=idx + 51,
            include_empty=True,
        )

    # Ambiguity guard: Megahub Jateng and Jatim are separate order lines.
    jateng = orders[3]
    jatim = orders[4]
    jatim_unit = UnitData("23:00", jatim.route, "AGUNG", "B 555 AX", "081574673448")
    jateng_unit = UnitData("23:00", jateng.route, "AGUS / DIAN", "AD 8857 DV", "+62 815-5952-1259")
    add_pair(
        rows,
        seen,
        order=jateng,
        incoming_order=jatim,
        units=[jatim_unit],
        label="NO_MATCH",
        pair_kind="negative_multi_line_wrong_route",
        action="DIFFERENT_ORDER_LINE",
        variant_index=70,
    )
    add_pair(
        rows,
        seen,
        order=jatim,
        incoming_order=jateng,
        units=[jateng_unit],
        label="NO_MATCH",
        pair_kind="negative_multi_line_wrong_route",
        action="DIFFERENT_ORDER_LINE",
        variant_index=71,
    )


def build_dataset() -> list[dict[str, object]]:
    random.seed(RANDOM_SEED)
    seeds = extract_seed_values(read_source_text())

    rows: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    add_explicit_case_pairs(rows, seen, seeds)

    base_orders = [*seed_orders(), *[make_random_order(seeds, i) for i in range(240)]]
    target_per_label = TARGET_ROWS // 2
    label_counts = Counter(row["label"] for row in rows)
    attempts = 0

    while len(rows) < TARGET_ROWS and attempts < TARGET_ROWS * 80:
        attempts += 1
        order = random.choice(base_orders)
        variant = attempts + len(rows)
        label_counts = Counter(row["label"] for row in rows)

        need_match = label_counts["MATCH"] < target_per_label
        need_no_match = label_counts["NO_MATCH"] < target_per_label

        if need_match and (not need_no_match or random.random() < 0.52):
            mode = random.choice(["fill", "no_header", "duplicate", "resend"])
            if mode == "duplicate" and order.existing_units:
                add_pair(
                    rows,
                    seen,
                    order=order,
                    incoming_order=order,
                    units=[random.choice(order.existing_units)],
                    label="MATCH",
                    pair_kind="positive_duplicate_resend",
                    action="DUPLICATE_EXISTING_UNIT",
                    variant_index=variant,
                    include_header=random.random() > 0.25,
                    include_order_meta=random.random() > 0.15,
                )
                continue

            fill_count = random.randint(1, max(1, min(3, order.remaining_slots)))
            fill_units = [
                random_unit(seeds, order, loading_time=random.choice(order.empty_times or seeds["times"]))
                for _ in range(fill_count)
            ]
            if mode == "resend" and order.existing_units:
                units = [*random.sample(list(order.existing_units), k=min(len(order.existing_units), random.randint(1, 2))), *fill_units]
                action = "RESEND_WITH_NEW_FILL"
            else:
                units = fill_units
                action = "NEW_FILL_SLOT"
            add_pair(
                rows,
                seen,
                order=order,
                incoming_order=order,
                units=units,
                label="MATCH",
                pair_kind=f"positive_{mode}",
                action=action,
                variant_index=variant,
                include_header=(mode != "no_header"),
                include_order_meta=random.random() > 0.1,
            )
            continue

        if need_no_match:
            mode = random.choice(["route", "location", "date", "unit_type", "cbm", "empty", "over_target"])
            if mode == "empty":
                empty_unit = UnitData(
                    random.choice(order.empty_times or seeds["times"]),
                    order.route,
                    "",
                    "",
                    "",
                )
                add_pair(
                    rows,
                    seen,
                    order=order,
                    incoming_order=order,
                    units=[empty_unit],
                    label="NO_MATCH",
                    pair_kind="negative_empty_incoming_unit",
                    action="EMPTY_SLOT",
                    variant_index=variant,
                    include_empty=True,
                )
                continue

            if mode == "over_target":
                complete_order = OrderState(
                    source_id=f"{order.source_id}_complete_state",
                    request_date=order.request_date,
                    qty_target=max(order.qty_target, max(1, order.complete_count)),
                    unit_type=order.unit_type,
                    cbm=order.cbm,
                    location=order.location,
                    route=order.route,
                    existing_units=tuple(
                        list(order.existing_units)
                        + [
                            random_unit(seeds, order, loading_time=random.choice(order.empty_times or seeds["times"]))
                            for _ in range(max(0, order.qty_target - order.complete_count))
                        ]
                    )[: order.qty_target],
                    empty_times=(),
                )
                add_pair(
                    rows,
                    seen,
                    order=complete_order,
                    incoming_order=complete_order,
                    units=[random_unit(seeds, complete_order)],
                    label="NO_MATCH",
                    pair_kind="negative_over_target_qty",
                    action="OVER_TARGET_QTY",
                    variant_index=variant,
                )
                continue

            wrong_order = mutate_order(order, seeds, mode)
            add_pair(
                rows,
                seen,
                order=order,
                incoming_order=wrong_order,
                units=[random_unit(seeds, wrong_order, loading_time=random.choice(wrong_order.empty_times or seeds["times"]))],
                label="NO_MATCH",
                pair_kind=f"negative_wrong_{mode}",
                action="DIFFERENT_ORDER",
                variant_index=variant,
                include_header=random.random() > 0.15,
                include_order_meta=random.random() > 0.05,
            )

    rows = rows[:TARGET_ROWS]
    for index, row in enumerate(rows, start=1):
        row["pair_id"] = f"stage2_completion_{index:04d}"
    return rows


def validate(rows: list[dict[str, object]]) -> None:
    if len(rows) != TARGET_ROWS:
        raise ValueError(f"Expected {TARGET_ROWS} rows, got {len(rows)}")
    labels = Counter(row["label"] for row in rows)
    if labels["MATCH"] != TARGET_ROWS // 2 or labels["NO_MATCH"] != TARGET_ROWS // 2:
        raise ValueError(f"Unbalanced labels: {dict(labels)}")
    for idx, row in enumerate(rows):
        for key in ("text_a", "text_b", "label"):
            if key not in row or not clean(str(row[key])):
                raise ValueError(f"Invalid row {idx}: missing {key}")
        if row["label"] not in {"MATCH", "NO_MATCH"}:
            raise ValueError(f"Invalid label at row {idx}: {row['label']}")


def main() -> None:
    rows = build_dataset()
    validate(rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    label_counts = Counter(row["label"] for row in rows)
    kind_counts = Counter(row["pair_kind"] for row in rows)
    action_counts = Counter(row["unit_action"] for row in rows)
    print(f"Output: {OUTPUT_PATH}")
    print(f"Total rows: {len(rows)}")
    print(f"Label distribution: {dict(label_counts)}")
    print(f"Top pair kinds: {dict(kind_counts.most_common(8))}")
    print(f"Unit actions: {dict(action_counts)}")


if __name__ == "__main__":
    main()
