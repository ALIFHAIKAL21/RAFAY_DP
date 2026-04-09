import argparse
import importlib.util
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
APP_COPY_PATH = ROOT_DIR / "app copy.py"
APP_MAIN_PATH = ROOT_DIR / "app.py"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.inference.batch_processor import ChatBatchProcessor


def load_app_copy_module():
    target_path = APP_COPY_PATH if APP_COPY_PATH.exists() else APP_MAIN_PATH
    spec = importlib.util.spec_from_file_location("app_copy_module", target_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def status_count(df):
    fields = ["DATE", "ORIGIN", "DESTINATION", "PLATE", "UNIT_TYPE", "DRIVER", "PHONE"]

    def is_filled(value):
        s = str(value or "").strip()
        return s not in {"", "None", "nan", "NaN", "NAN"}

    out = {"ASSIGNED": 0, "PARTIAL": 0, "UNASSIGNED": 0}
    for _, row in df.iterrows():
        filled = sum(1 for f in fields if is_filled(row.get(f, "")))
        if filled >= 7:
            out["ASSIGNED"] += 1
        elif filled >= 3:
            out["PARTIAL"] += 1
        else:
            out["UNASSIGNED"] += 1
    return out


def run_pipeline(app_mod, input_text: str, temp_txt_path: Path, temp_xlsx_path: Path):
    temp_txt_path.write_text(input_text, encoding="utf-8")

    processor = ChatBatchProcessor(
        model_path=Path(app_mod.APP_MODEL_PATH) if app_mod.APP_MODEL_PATH else None,
        event_model_path=app_mod.APP_EVENT_MODEL_PATH if app_mod.APP_EVENT_MODEL_PATH else None,
        event_threshold=app_mod.APP_EVENT_THRESHOLD,
    )
    df_raw = processor.process_file(str(temp_txt_path), output_excel=str(temp_xlsx_path))
    if df_raw is None or df_raw.empty:
        return None, None

    df_before = app_mod.enforce_block_quota(app_mod.preprocess_context(df_raw.copy()))
    df_after = app_mod.apply_revisions_from_chat(input_text, df_before.copy())
    df_after = app_mod.apply_driver_pair_from_text(df_after)
    df_after = app_mod.apply_phone_pair_from_text(df_after)
    if "PLATE" in df_after.columns:
        df_after["PLATE"] = df_after["PLATE"].apply(app_mod.clean_plate_value)
    return df_before, df_after


def main():
    parser = argparse.ArgumentParser(description="Run refill/revision ML test against app copy.py")
    parser.add_argument(
        "--day1",
        default="tests/masive _test/refill test/day1_neworder_day2_fillpartial_30/tc_day1_full_new_order_30.txt",
        help="Path file Day 1 full new order",
    )
    parser.add_argument(
        "--day2",
        default="tests/masive _test/refill test/day1_neworder_day2_fillpartial_30/tc_day2_full_fill_partial_20.txt",
        help="Path file Day 2 refill",
    )
    parser.add_argument(
        "--out-dir",
        default="tests/outputs",
        help="Output directory for CSV results",
    )
    args = parser.parse_args()

    app_mod = load_app_copy_module()

    day1_path = (ROOT_DIR / args.day1).resolve()
    day2_path = (ROOT_DIR / args.day2).resolve()
    out_dir = (ROOT_DIR / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not day1_path.exists():
        raise FileNotFoundError(f"Day1 file tidak ditemukan: {day1_path}")
    if not day2_path.exists():
        raise FileNotFoundError(f"Day2 file tidak ditemukan: {day2_path}")

    day1_text = day1_path.read_text(encoding="utf-8")
    day2_text = day2_path.read_text(encoding="utf-8")
    combined_text = f"{day1_text}\n\n{day2_text}"

    temp_txt = out_dir / "_temp_refill_case_input.txt"
    temp_xlsx = out_dir / "_temp_refill_case_output.xlsx"

    df_before, df_after = run_pipeline(app_mod, combined_text, temp_txt, temp_xlsx)
    if df_before is None or df_after is None:
        print("Tidak ada output dari parser.")
        return

    before_stat = status_count(df_before)
    after_stat = status_count(df_after)
    print(f"[BEFORE] rows={len(df_before)} stats={before_stat}")
    print(f"[AFTER ] rows={len(df_after)} stats={after_stat}")

    before_csv = out_dir / "refill_ml_app_copy_before.csv"
    after_csv = out_dir / "refill_ml_app_copy_after.csv"
    df_before.to_csv(before_csv, index=False, encoding="utf-8-sig")
    df_after.to_csv(after_csv, index=False, encoding="utf-8-sig")
    print(f"[OUT] BEFORE CSV: {before_csv}")
    print(f"[OUT] AFTER  CSV: {after_csv}")

    try:
        temp_txt.unlink()
    except Exception:
        pass
    try:
        temp_xlsx.unlink()
    except Exception:
        pass


if __name__ == "__main__":
    main()
