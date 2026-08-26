#!/usr/bin/env python3
"""Desktop launcher for the standalone Delivery Gantt app."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


APP_NAME = "Delivery Gantt"


def source_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[1]


def default_data_dir() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library/Application Support" / APP_NAME
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", home / "AppData/Roaming")) / APP_NAME
    return Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")) / APP_NAME


def load_server_module(root: Path):
    path = root / "scripts/serve-delivery-dashboard.py"
    spec = importlib.util.spec_from_file_location("serve_delivery_dashboard", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_seed_portable(root: Path, portable_dir: Path, reset: bool = False) -> None:
    seed = root / "portable/gantt/latest"
    if not seed.exists():
        raise FileNotFoundError(f"Missing bundled portable snapshot: {seed}")
    if reset and portable_dir.exists():
        shutil.rmtree(portable_dir)
    if portable_dir.exists() and (portable_dir / "gantt-local-edits.json").exists():
        return
    portable_dir.mkdir(parents=True, exist_ok=True)
    for item in seed.iterdir():
        target = portable_dir / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        elif item.is_file():
            shutil.copy2(item, target)


def bind_server(server_module, host: str, preferred_port: int, delivery_dir: Path, portable_dir: Path):
    server_module.DeliveryHandler.portable_directory = portable_dir
    server_module.prepare_directory_from_portable(delivery_dir, portable_dir)

    def handler(*handler_args, **handler_kwargs):
        return server_module.DeliveryHandler(*handler_args, directory=str(delivery_dir), **handler_kwargs)

    try:
        return server_module.ThreadingHTTPServer((host, preferred_port), handler)
    except OSError:
        if preferred_port == 0:
            raise
        return server_module.ThreadingHTTPServer((host, 0), handler)


def wait_until_ready(host: str, port: int, timeout: float = 4.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Start the standalone Delivery Gantt desktop app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--reset-data", action="store_true")
    args = parser.parse_args()

    root = source_root()
    data_dir = Path(args.data_dir).expanduser() if args.data_dir else default_data_dir()
    delivery_dir = data_dir / "exports/delivery"
    portable_dir = data_dir / "portable/gantt/latest"
    data_dir.mkdir(parents=True, exist_ok=True)

    copy_seed_portable(root, portable_dir, reset=args.reset_data)
    server_module = load_server_module(root)
    server = bind_server(server_module, args.host, args.port, delivery_dir, portable_dir)
    host, port = server.server_address
    url = f"http://{host}:{port}/gantt.html"

    if not args.no_browser:
        threading.Thread(target=lambda: (wait_until_ready(host, port), webbrowser.open(url)), daemon=True).start()

    print(f"{APP_NAME} is running at {url}", flush=True)
    print(f"Data directory: {data_dir}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
