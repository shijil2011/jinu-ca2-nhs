"""Download the aggregator's rolling ~30-day hourly history.

Run today, then once a week (Sundays), so older hours are not lost.
Listed in https://checkwaitingtimes.co.uk/llms.txt
  https://live.checkwaitingtimes.co.uk/history/{source_id}.json
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.environ.get("AE_HISTORY_DIR", ROOT / "data" / "nhs" / "history_raw"))
DEFAULT_UA = "jinu-ca2-ae/1.0 (DBS MSc student project)"
USER_AGENT = os.environ.get("AE_USER_AGENT") or DEFAULT_UA
HISTORY_URL = "https://live.checkwaitingtimes.co.uk/history/{source}.json"
SOURCES = [
    "uhcw", "plymouth", "torbay", "mcht", "swbh", "mkuh", "uhb", "whh",
    "wyevalley", "ncic", "cornwall", "southamptonutc",
]


def run():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = {}
    for src in SOURCES:
        try:
            resp = requests.get(
                HISTORY_URL.format(source=src),
                headers={"User-Agent": USER_AGENT},
                timeout=30,
            )
            resp.raise_for_status()
            payload = resp.json()
            out = OUT_DIR / src / f"{today}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(payload), encoding="utf-8")
            n_sites = len((payload or {}).get("sites") or {})
            summary[src] = {"http_status": resp.status_code, "sites": n_sites}
        except Exception as exc:
            summary[src] = {"error": f"{type(exc).__name__}: {exc}"[:160]}
        time.sleep(1)  # be polite
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
