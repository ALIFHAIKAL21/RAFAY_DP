from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent

STRICT_NEW_ORDER_INPUT = ROOT_DIR / "pesanan_baru" / "stress_test.txt"
STRICT_FOLLOWUP_INPUT = ROOT_DIR / "pesanan_susulan" / "stress_test.txt"

FALLBACK_INPUTS = {
    STRICT_NEW_ORDER_INPUT: [
        ROOT_DIR / "test_case" / "pesanan_baru" / "stress_test.txt",
    ],
    STRICT_FOLLOWUP_INPUT: [
        ROOT_DIR / "test_case" / "pesanan_susulan" / "pelengkapan" / "stress_test.txt",
        ROOT_DIR / "test_case" / "pesanan_susulan" / "revisi" / "test_case_r01.txt",
    ],
}

OUTPUT_PATH = ROOT_DIR / "chat" / "processed" / "spc" / "final_dataset.json"
COMPAT_OUTPUT_PATH = ROOT_DIR / "data" / "chat" / "processed" / "SPC" / "final_dataset.json"


HEADERS = [
    "REQUEST ORDER ONCALL",
    "Request Unit On Call",
    "REQUEST ULANG ORDER",
    "REQUEST ORDER ULANG ONCALL",
    "Request Ulang Order On Call",
    "REQUER ORDER ULANG DAN TAMBAHAN",
    "REQUER ORDER ULANG DAN TAMBAHAN ON CALL",
]

DRIVERS = [
    "ANDI",
    "JOKO",
    "SAMSUL",
    "YANTO",
    "BUDI",
    "OZAN",
    "SENO",
    "HENDRA",
]

PLATES = [
    "B 1111 AA",
    "L 674 BB",
    "A 765 AX",
    "D 4321 EF",
    "B 4322 AA",
    "D 9044 AG",
    "L 990 UX",
    "B 890 AA",
]


@dataclass(frozen=True)
class Slot:
    location: str
    loading_time: str
    route: str
    unit_type: str
    status: str = "KOSONG"
    driver: str = "-"
    plate: str = "-"


BASE_SLOTS = [
    Slot("ARGOPANTES", "18:00", "CGK-SUB", "TWB"),
    Slot("ARGOPANTES", "21:00", "CGK-SUB", "TWB"),
    Slot("ARGOPANTES", "00:00", "CGK-SUB", "TWB"),
    Slot("ARGOPANTES", "03:00", "CGK-SUB", "TWB"),
]

REVISION_SLOT = Slot(
    location="ARGOPANTES",
    loading_time="SEGERA",
    route="CGK-SUB",
    unit_type="TWB",
    status="TERISI",
    driver="HENDRA",
    plate="D 9044 AG",
)


def read_text_if_available(primary_path: Path) -> tuple[Path | None, str]:
    for candidate_path in [primary_path, *FALLBACK_INPUTS.get(primary_path, [])]:
        if candidate_path.exists():
            return candidate_path, candidate_path.read_text(encoding="utf-8")
    return None, ""


def route_with_spaces(route: str) -> str:
    return route.replace("-", " - ")


def render_slot_text(slot: Slot, template_index: int) -> str:
    templates = [
        (
            "DB_SLOT | Lokasi: {location} | Waktu Loading: {loading_time} | "
            "Rute: {route} | Unit: {unit_type} | Status: {status} | "
            "Driver: {driver} | Nopol: {plate}"
        ),
        (
            "Baris database {status}: {location} | {loading_time} | {route} | "
            "{unit_type} | driver {driver} | nopol {plate}"
        ),
        (
            "SLOT EXCEL | Pickup={location}; Jam={loading_time}; "
            "Tujuan={route}; Tipe Unit={unit_type}; Status={status}"
        ),
        (
            "1 baris armada | Lokasi : {location} | Waktu : {loading_time} | "
            "Rute/tujuan : {route} | Type Truck : {unit_type} | "
            "Driver : {driver} | Nopol : {plate}"
        ),
    ]
    return templates[template_index % len(templates)].format(
        location=slot.location,
        loading_time=slot.loading_time,
        route=slot.route,
        unit_type=slot.unit_type,
        status=slot.status,
        driver=slot.driver,
        plate=slot.plate,
    )


def render_followup_single(
    *,
    header: str,
    slot: Slot,
    driver: str,
    plate: str,
    template_index: int,
    include_location: bool = True,
    include_unit_type: bool = True,
) -> str:
    unit_line = f"1 UNIT {slot.unit_type} | " if include_unit_type else ""
    location_line = f"Lokasi: {slot.location} | " if include_location else ""
    route_spaced = route_with_spaces(slot.route)
    templates = [
        (
            "{header} | {unit_line}{location_line}Waktu loading : {loading_time} | "
            "Rute/tujuan : {route_spaced} | driver : {driver} | Nopol : {plate}"
        ),
        (
            "{header}\n{unit_line}{location_line}Waktu: {loading_time}\n"
            "Rute: {route}\nDriver: {driver}\nNopol: {plate}"
        ),
        (
            "{header} - {unit_line}{location_line}Jam muat {loading_time}; "
            "tujuan {route}; driver {driver}; nopol {plate}"
        ),
    ]
    return templates[template_index % len(templates)].format(
        header=header,
        unit_line=unit_line,
        location_line=location_line,
        loading_time=slot.loading_time,
        route=slot.route,
        route_spaced=route_spaced,
        driver=driver,
        plate=plate,
    )


def render_followup_multi(header: str, slots: list[Slot], template_index: int) -> str:
    if template_index % 2 == 0:
        blocks = [
            f"Waktu: {slot.loading_time} Rute: {slot.route} Driver: {DRIVERS[slot_index % len(DRIVERS)]}"
            for slot_index, slot in enumerate(slots)
        ]
        return f"{header} | " + " | ".join(blocks)

    blocks = [
        (
            f"Lokasi: {slot.location}\n"
            f"Waktu loading : {slot.loading_time}\n"
            f"Rute/tujuan : {route_with_spaces(slot.route)}\n"
            f"Driver : {DRIVERS[slot_index % len(DRIVERS)]}"
        )
        for slot_index, slot in enumerate(slots)
    ]
    return f"{header}\n1 UNIT {slots[0].unit_type}\n" + "\n---\n".join(blocks)


def render_revision_slot(template_index: int) -> str:
    templates = [
        (
            "DB_TERISI | Lokasi: {location} | Waktu Loading: {loading_time} | "
            "Rute: {route} | Unit: {unit_type} | Driver: {driver} | "
            "Nopol Lama/Riwayat: {plate} | Status: {status}"
        ),
        (
            "Baris database sudah terisi | {location} | {loading_time} | {route} | "
            "{unit_type} | Driver {driver} | Nopol {plate}"
        ),
        (
            "Riwayat order: pickup {location}; jam {loading_time}; tujuan {route}; "
            "unit {unit_type}; nopol aktif/lama {plate}; driver {driver}"
        ),
    ]
    return templates[template_index % len(templates)].format(
        location=REVISION_SLOT.location,
        loading_time=REVISION_SLOT.loading_time,
        route=REVISION_SLOT.route,
        unit_type=REVISION_SLOT.unit_type,
        driver=REVISION_SLOT.driver,
        plate=REVISION_SLOT.plate,
        status=REVISION_SLOT.status,
    )


def render_revision_message(old_plate: str, new_plate: str, driver: str, template_index: int) -> str:
    templates = [
        f"REVISI NOPOL {old_plate} driver {driver} Nopol {new_plate}",
        f"Revisi unit lama {old_plate} ganti nopol {new_plate} driver {driver}",
        f"INFO REVISI | Nopol sebelumnya: {old_plate} | Driver: {driver} | Nopol baru: {new_plate}",
    ]
    return templates[template_index % len(templates)]


def append_pair(rows: list[dict[str, object]], text_a: str, text_b: str, label: int) -> None:
    rows.append(
        {
            "text_a": " ".join(text_a.split()),
            "text_b": " ".join(text_b.split()),
            "label": int(label),
        }
    )


def add_required_cases(rows: list[dict[str, object]]) -> None:
    append_pair(
        rows,
        render_slot_text(BASE_SLOTS[0], 0),
        (
            "REQUER ORDER ULANG DAN TAMBAHAN ON CALL | Waktu loading : 18:00 | "
            "Rute/tujuan : CGK - SUB | driver : ANDI"
        ),
        1,
    )
    append_pair(
        rows,
        render_slot_text(BASE_SLOTS[1], 0),
        (
            "REQUEST ORDER ULANG ONCALL | Waktu loading : 18:00 | "
            "Rute/tujuan : CGK - SUB | driver : ANDI"
        ),
        0,
    )
    append_pair(
        rows,
        render_slot_text(BASE_SLOTS[2], 0),
        (
            "Request Unit On Call | Waktu: 21:00 Rute: CGK-SUB Driver: | "
            "Waktu: 00:00 Rute: CGK-SUB Driver: JOKO | "
            "Waktu: 03:00 Rute: CGK-SUB Driver:"
        ),
        1,
    )
    append_pair(
        rows,
        render_slot_text(BASE_SLOTS[3], 0),
        (
            "REQUEST ORDER ONCALL | 1 UNIT CDDL | Lokasi: CIKARANG | "
            "Waktu: 03:00 | Rute: CGK-SUB | driver: SAMSUL"
        ),
        0,
    )
    append_pair(
        rows,
        render_revision_slot(0),
        "REVISI NOPOL D 9044 AG driver YANTO Nopol B 1111 AA",
        1,
    )


def add_single_slot_cases(rows: list[dict[str, object]]) -> None:
    for header_index, header in enumerate(HEADERS):
        for slot_index, slot in enumerate(BASE_SLOTS):
            text_a = render_slot_text(slot, header_index + slot_index)
            driver = DRIVERS[(header_index + slot_index) % len(DRIVERS)]
            plate = PLATES[(header_index + slot_index) % len(PLATES)]

            append_pair(
                rows,
                text_a,
                render_followup_single(
                    header=header,
                    slot=slot,
                    driver=driver,
                    plate=plate,
                    template_index=header_index,
                    include_location=True,
                    include_unit_type=True,
                ),
                1,
            )

            append_pair(
                rows,
                text_a,
                render_followup_single(
                    header=header,
                    slot=slot,
                    driver=driver,
                    plate=plate,
                    template_index=header_index + 1,
                    include_location=False,
                    include_unit_type=False,
                ),
                1,
            )

            wrong_time_slot = BASE_SLOTS[(slot_index + 1) % len(BASE_SLOTS)]
            wrong_time_same_order = Slot(
                location=slot.location,
                loading_time=wrong_time_slot.loading_time,
                route=slot.route,
                unit_type=slot.unit_type,
            )
            append_pair(
                rows,
                text_a,
                render_followup_single(
                    header=header,
                    slot=wrong_time_same_order,
                    driver=driver,
                    plate=plate,
                    template_index=header_index + 2,
                    include_location=True,
                    include_unit_type=True,
                ),
                0,
            )

            wrong_route_slot = Slot(
                location=slot.location,
                loading_time=slot.loading_time,
                route="CGK-MES",
                unit_type=slot.unit_type,
            )
            append_pair(
                rows,
                text_a,
                render_followup_single(
                    header=header,
                    slot=wrong_route_slot,
                    driver=driver,
                    plate=plate,
                    template_index=header_index,
                    include_location=True,
                    include_unit_type=True,
                ),
                0,
            )

            wrong_contract_slot = Slot(
                location="CIKARANG",
                loading_time=slot.loading_time,
                route=slot.route,
                unit_type="CDDL",
            )
            append_pair(
                rows,
                text_a,
                render_followup_single(
                    header=header,
                    slot=wrong_contract_slot,
                    driver=driver,
                    plate=plate,
                    template_index=header_index + 1,
                    include_location=True,
                    include_unit_type=True,
                ),
                0,
            )


def add_multi_schedule_cases(rows: list[dict[str, object]]) -> None:
    for header_index, header in enumerate(HEADERS):
        for slot_index, target_slot in enumerate(BASE_SLOTS):
            text_a = render_slot_text(target_slot, header_index + slot_index + 1)
            ordered_slots = [
                BASE_SLOTS[(slot_index + offset) % len(BASE_SLOTS)]
                for offset in range(len(BASE_SLOTS))
            ]
            append_pair(
                rows,
                text_a,
                render_followup_multi(header, ordered_slots, header_index),
                1,
            )

            omitted_target_slots = [
                candidate_slot
                for candidate_slot in BASE_SLOTS
                if candidate_slot.loading_time != target_slot.loading_time
            ]
            append_pair(
                rows,
                text_a,
                render_followup_multi(header, omitted_target_slots, header_index + 1),
                0,
            )

            wrong_location_blocks = [
                Slot("CIKARANG", slot.loading_time, slot.route, slot.unit_type)
                for slot in ordered_slots
            ]
            append_pair(
                rows,
                text_a,
                render_followup_multi(header, wrong_location_blocks, header_index + 2),
                0,
            )


def add_revision_cases(rows: list[dict[str, object]]) -> None:
    revision_headers = [
        "",
        "REQUEST ORDER ONCALL | ",
        "REQUEST ULANG ORDER | ",
        "REQUER ORDER ULANG DAN TAMBAHAN | ",
    ]
    for header_index, header in enumerate(revision_headers):
        text_a = render_revision_slot(header_index)

        append_pair(
            rows,
            text_a,
            header + render_revision_message("D 9044 AG", "B 1111 AA", "YANTO", header_index),
            1,
        )
        append_pair(
            rows,
            text_a,
            header + render_revision_message("D 9044 AG", "B 890 AA", "HENDRA", header_index + 1),
            1,
        )
        append_pair(
            rows,
            text_a,
            header + render_revision_message("L 9511 AL", "B 1111 AA", "YANTO", header_index + 2),
            0,
        )
        append_pair(
            rows,
            text_a,
            header + "REVISI NOPOL B 2222 BB driver YANTO Nopol B 1111 AA",
            0,
        )


def dedupe_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    seen_keys = set()
    unique_rows = []
    for row in rows:
        key = (row["text_a"], row["text_b"], row["label"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_rows.append(row)
    return unique_rows


def build_dataset() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    add_required_cases(rows)
    add_single_slot_cases(rows)
    add_multi_schedule_cases(rows)
    add_revision_cases(rows)
    return dedupe_rows(rows)


def validate_dataset(rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("Dataset kosong.")

    required_keys = {"text_a", "text_b", "label"}
    for row_index, row in enumerate(rows):
        if set(row.keys()) != required_keys:
            raise ValueError(f"Baris {row_index} tidak memakai schema wajib: {row}")
        if not isinstance(row["text_a"], str) or not row["text_a"].strip():
            raise ValueError(f"text_a kosong pada baris {row_index}")
        if not isinstance(row["text_b"], str) or not row["text_b"].strip():
            raise ValueError(f"text_b kosong pada baris {row_index}")
        if row["label"] not in {0, 1}:
            raise ValueError(f"Label harus 0/1 pada baris {row_index}: {row['label']}")

    label_counts = Counter(row["label"] for row in rows)
    if set(label_counts) != {0, 1}:
        raise ValueError(f"Dataset harus punya label 0 dan 1: {dict(label_counts)}")


def write_json(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_dataset(rows: list[dict[str, object]]) -> None:
    write_json(rows, OUTPUT_PATH)
    write_json(rows, COMPAT_OUTPUT_PATH)


def main() -> None:
    input_sources = {
        "pesanan_baru": read_text_if_available(STRICT_NEW_ORDER_INPUT),
        "pesanan_susulan": read_text_if_available(STRICT_FOLLOWUP_INPUT),
    }
    for source_name, (source_path, source_text) in input_sources.items():
        if source_path is None:
            print(f"Input {source_name}: tidak ditemukan, lanjut pakai skenario sintetis.")
        else:
            print(f"Input {source_name}: {source_path} ({len(source_text)} karakter)")

    rows = build_dataset()
    validate_dataset(rows)
    write_dataset(rows)

    label_counts = Counter(row["label"] for row in rows)
    print(f"Output wajib: {OUTPUT_PATH}")
    print(f"Output kompatibel IDE: {COMPAT_OUTPUT_PATH}")
    print(f"Total pairs: {len(rows)}")
    print(f"Label distribution: {dict(sorted(label_counts.items()))}")


if __name__ == "__main__":
    main()
