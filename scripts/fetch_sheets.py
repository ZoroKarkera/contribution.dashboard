from __future__ import annotations

import json
import importlib
import os
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def build_auth_header() -> str | None:
    credentials_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not credentials_json:
        return None

    try:
        requests_module = importlib.import_module("google.auth.transport.requests")
        service_account_module = importlib.import_module("google.oauth2.service_account")
    except ImportError as exc:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is set but google-auth is not installed. "
            "Install it with: pip install google-auth"
        ) from exc

    request_cls = getattr(requests_module, "Request")
    credentials_cls = getattr(service_account_module, "Credentials")

    credentials_info = json.loads(credentials_json)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    credentials = credentials_cls.from_service_account_info(credentials_info, scopes=scopes)
    credentials.refresh(request_cls())
    return f"Bearer {credentials.token}"


def download_csv(url: str, destination: Path, auth_header: str | None = None) -> None:
    if not url:
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url)
    if auth_header:
        request.add_header("Authorization", auth_header)

    try:
        with urllib.request.urlopen(request) as response:
            destination.write_bytes(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise RuntimeError(
                "Unauthorized while downloading Google Sheet CSV. "
                "For private sheets, set GOOGLE_SERVICE_ACCOUNT_JSON in GitHub Secrets "
                "and share the sheet with that service account email."
            ) from exc
        raise


def main() -> None:
    auth_header = build_auth_header()
    download_csv(os.getenv("OWNERS_CSV_URL", "").strip(), DATA_DIR / "owners.csv", auth_header)
    download_csv(os.getenv("RESPONSE_CSV_URL", "").strip(), DATA_DIR / "response.csv", auth_header)


if __name__ == "__main__":
    main()
