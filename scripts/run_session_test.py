from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from session_test_runtime import (
    ROOT_DIR,
    ensure_session_test_database,
    masked_url,
    port_is_available,
    resolve_session_test_database,
)


DEFAULT_APP = ROOT_DIR / "stage2_pair_visual_test copy.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Jalankan aplikasi pengujian sesi dengan database terisolasi."
    )
    parser.add_argument("--port", type=int, default=8502)
    parser.add_argument("--address", default="127.0.0.1")
    parser.add_argument("--app", type=Path, default=DEFAULT_APP)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app_path = args.app.resolve()
    if not app_path.exists():
        raise FileNotFoundError(f"File aplikasi test tidak ditemukan: {app_path}")
    if not 1 <= args.port <= 65535:
        raise ValueError(f"Port tidak valid: {args.port}")
    if not port_is_available(args.address, args.port):
        raise RuntimeError(
            f"Port {args.address}:{args.port} sedang digunakan. "
            "Hentikan proses lama atau pilih --port lain."
        )

    config = resolve_session_test_database()
    created = ensure_session_test_database(config)

    env = os.environ.copy()
    env["DATABASE_URL"] = config.target_url.render_as_string(hide_password=False)
    env["IDP_SESSION_TEST_MODE"] = "1"
    env["IDP_SESSION_TEST_DB_NAME"] = config.database_name
    env["IDP_SESSION_TEST_PORT"] = str(args.port)
    env["IDP_APP_ENV"] = "session_test"

    schema_check = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from db.session_workspace import init_workspace_registry; "
                "raise SystemExit(0 if init_workspace_registry() else 1)"
            ),
        ],
        cwd=ROOT_DIR,
        env=env,
        check=False,
    )
    if schema_check.returncode != 0:
        raise RuntimeError("Inisialisasi registry workspace session test gagal.")

    state = "dibuat" if created else "sudah tersedia"
    print(f"[session-test] Database {config.database_name} {state}.")
    print("[session-test] Registry workspace test siap.")
    print(f"[session-test] Koneksi: {masked_url(config.target_url)}")
    print(f"[session-test] Aplikasi: http://localhost:{args.port}")
    print("[session-test] Tekan Ctrl+C untuk menghentikan server.")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(args.port),
        "--server.address",
        args.address,
        "--browser.gatherUsageStats",
        "false",
    ]
    completed = subprocess.run(command, cwd=ROOT_DIR, env=env, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
