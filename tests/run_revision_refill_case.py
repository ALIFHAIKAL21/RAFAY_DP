import argparse
from pathlib import Path

import pandas as pd

from src.inference.batch_processor import ChatBatchProcessor
from app import (
    apply_driver_pair_from_text,
    apply_phone_pair_from_text,
    apply_revisions_from_chat,
    clean_plate_value,
    enforce_block_quota,
    preprocess_context,
)


def _is_filled(value):
    if value is None:
        return False
    s = str(value).strip()
    return s not in {"", "-", "null", "none", "nan", "undefined"}


def _status_row(row):
    fields = ["DATE", "ORIGIN", "DESTINATION", "PLATE", "UNIT_TYPE", "DRIVER", "PHONE"]
    filled = sum(1 for f in fields if _is_filled(row.get(f)))
    if filled >= 7:
        return "ASSIGNED"
    if filled >= 3:
        return "PARTIAL"
    return "UNASSIGNED"


def _field_fill_count(df, field):
    if field not in df.columns:
        return 0
    return int(df[field].apply(_is_filled).sum())


def run_case(input_path, model_path, event_model_path, event_threshold, out_csv):
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"File test tidak ditemukan: {input_file}")

    with open(input_file, "r", encoding="utf-8") as f:
        chat_text = f.read()

    processor = ChatBatchProcessor(
        model_path=model_path,
        event_model_path=event_model_path,
        event_threshold=event_threshold,
    )

    df_raw = processor.process_file(str(input_file), output_excel="temp_revision_refill_case.xlsx")
    if df_raw is None or df_raw.empty:
        print("Tidak ada row yang berhasil diekstrak.")
        return

    df_before = enforce_block_quota(preprocess_context(df_raw))
    df_after = apply_revisions_from_chat(chat_text, df_before.copy())
    df_after = apply_driver_pair_from_text(df_after)
    df_after = apply_phone_pair_from_text(df_after)
    if "PLATE" in df_after.columns:
        df_after["PLATE"] = df_after["PLATE"].apply(clean_plate_value)

    for df_name, df in [("BEFORE", df_before), ("AFTER", df_after)]:
        df["status_unit"] = df.apply(_status_row, axis=1)
        assigned = int((df["status_unit"] == "ASSIGNED").sum())
        partial = int((df["status_unit"] == "PARTIAL").sum())
        unassigned = int((df["status_unit"] == "UNASSIGNED").sum())
        print(f"[{df_name}] rows={len(df)} assigned={assigned} partial={partial} unassigned={unassigned}")
        print(
            f"[{df_name}] fill DRIVER={_field_fill_count(df, 'DRIVER')} "
            f"PLATE={_field_fill_count(df, 'PLATE')} PHONE={_field_fill_count(df, 'PHONE')}"
        )

    before_map = {}
    after_map = {}
    for i in range(len(df_before)):
        before_map[i] = (
            str(df_before.at[i, "DRIVER"]) if "DRIVER" in df_before.columns else "",
            str(df_before.at[i, "PLATE"]) if "PLATE" in df_before.columns else "",
            str(df_before.at[i, "PHONE"]) if "PHONE" in df_before.columns else "",
        )
    for i in range(len(df_after)):
        after_map[i] = (
            str(df_after.at[i, "DRIVER"]) if "DRIVER" in df_after.columns else "",
            str(df_after.at[i, "PLATE"]) if "PLATE" in df_after.columns else "",
            str(df_after.at[i, "PHONE"]) if "PHONE" in df_after.columns else "",
        )

    changed = sum(1 for i in before_map if before_map.get(i) != after_map.get(i))
    print(f"[DIFF] row berubah karena revisi/refill: {changed}")

    if out_csv:
        out_path = Path(out_csv)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_after.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"[OUT] hasil AFTER disimpan ke: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Runner test case revisi + refill partial.")
    parser.add_argument("--input", required=True, help="Path file txt test case")
    parser.add_argument("--model", default="models/indobert_NER/final_model", help="Path model NER")
    parser.add_argument(
        "--event-model",
        default="models/indobert_event_classifier/final_model",
        help="Path model event classifier",
    )
    parser.add_argument("--event-threshold", type=float, default=0.75, help="Threshold skip NON_ORDER")
    parser.add_argument("--out-csv", default="", help="Path output CSV final (opsional)")
    args = parser.parse_args()

    run_case(
        input_path=args.input,
        model_path=args.model,
        event_model_path=args.event_model,
        event_threshold=args.event_threshold,
        out_csv=args.out_csv,
    )


if __name__ == "__main__":
    main()
