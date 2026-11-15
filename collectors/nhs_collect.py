"""Save one snapshot of the live NHS A&E waiting-times feed.

Run:  python collectors/nhs_collect.py
Optional: set AE_USER_AGENT to a custom User-Agent (a default is used otherwise).
"""
import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

FEED_URL = "https://live.checkwaitingtimes.co.uk/ae.json"
ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = Path(os.environ.get("AE_CSV_DIR", ROOT / "data" / "nhs" / "readings_csv"))
LOG_PATH = Path(os.environ.get("AE_LOG_PATH", ROOT / "logs" / "nhs_collection_log.csv"))
DEFAULT_UA = "jinu-ca2-ae/1.0 (DBS MSc student project)"
USER_AGENT = os.environ.get("AE_USER_AGENT") or DEFAULT_UA

FIELDS = [
    "collected_at", "feed_generated_at", "site_id", "site_name", "trust_code",
    "source_id", "kind", "is_open", "wait_minutes", "wait_band_text",
    "patients_waiting", "patients_in_dept", "source_as_of", "is_stale",
]


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def flatten(site, collected_at, generated_at):
    band = site.get("wait_band") or {}
    is_open = site.get("open")
    return {
        "collected_at": collected_at,
        "feed_generated_at": generated_at,
        "site_id": f"{site.get('source_id')}:{slugify(site.get('name'))}",
        "site_name": site.get("name"),
        "trust_code": site.get("trust"),
        "source_id": site.get("source_id"),
        "kind": site.get("kind"),
        "is_open": "" if is_open is None else int(bool(is_open)),
        "wait_minutes": site.get("wait_minutes") if site.get("wait_minutes") is not None else "",
        "wait_band_text": band.get("text") or "",
        "patients_waiting": site.get("waiting") if site.get("waiting") is not None else "",
        "patients_in_dept": site.get("in_department") if site.get("in_department") is not None else "",
        "source_as_of": site.get("as_of"),
        "is_stale": int(bool(site.get("stale"))),
    }


def existing_keys(path):
    keys = set()
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("site_id"), row.get("source_as_of")))
    return keys


def append_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerows(rows)
    return path


def write_log(entry):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = ["run_at_utc", "status", "http_status", "sites_received", "rows_new", "rows_duplicate", "error"]
    new_file = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            w.writeheader()
        w.writerow({k: entry.get(k, "") for k in fields})


def run_once():
    collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {"run_at_utc": collected_at, "status": "error"}
    try:
        resp = requests.get(FEED_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("sites"), list):
            raise ValueError("unexpected JSON shape")
        rows = [flatten(s, collected_at, payload.get("generated_at")) for s in payload["sites"]]
        path = CSV_DIR / f"{collected_at[:10]}.csv"
        seen = existing_keys(path)
        new_rows = [r for r in rows if (r["site_id"], r["source_as_of"]) not in seen]
        append_csv(path, new_rows)
        entry.update(
            status="ok",
            http_status=resp.status_code,
            sites_received=len(rows),
            rows_new=len(new_rows),
            rows_duplicate=len(rows) - len(new_rows),
        )
    except Exception as exc:
        entry["error"] = f"{type(exc).__name__}: {exc}"[:300]
    write_log(entry)
    return entry


if __name__ == "__main__":
    print(run_once())
