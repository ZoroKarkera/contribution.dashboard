from __future__ import annotations

import os
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def download_csv(url: str, destination: Path) -> None:
    if not url:
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        destination.write_bytes(response.read())


def main() -> None:
    download_csv(os.getenv("OWNERS_CSV_URL", "").strip(), DATA_DIR / "owners.csv")
    download_csv(os.getenv("RESPONSE_CSV_URL", "").strip(), DATA_DIR / "response.csv")


if __name__ == "__main__":
    main()
