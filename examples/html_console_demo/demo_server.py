"""Run the standard-library Citta Console demo server."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from citta_console.server import run_server

CONFIG_PATH = ROOT / "examples" / "generic_jsonl" / "citta_config.json"


def main() -> None:
    run_server(config_path=str(CONFIG_PATH))


if __name__ == "__main__":
    main()
