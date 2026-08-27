"""Download BTS Reporting Carrier On-Time Performance monthly zips.

One zip per month (~25-32 MB) from the TranStats PREZIP mirror. Sequential and
polite (single connection, backoff on failure). Failed or interrupted downloads
are discarded, not resumed; re-running re-fetches anything missing and skips
files already present.

Usage:
    uv run python src/ingest/download_bts.py                    # 2015-2019
    uv run python src/ingest/download_bts.py --start 2015 --end 2025
    uv run python src/ingest/download_bts.py --start 2026 --end 2026 --months 1-6
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

BASE_URL = (
    "https://transtats.bts.gov/PREZIP/"
    "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
)
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
RETRIES = 3
BACKOFF_S = 10
# Monthly zips are ~25-32 MB; anything tiny would be an HTML error page, not data.
MIN_EXPECTED_BYTES = 1_000_000
TIMEOUT_S = 180


def download_month(session: requests.Session, year: int, month: int) -> str:
    url = BASE_URL.format(year=year, month=month)
    dest = RAW_DIR / url.rsplit("/", 1)[-1]
    if dest.exists() and dest.stat().st_size >= MIN_EXPECTED_BYTES:
        return "skip"

    for attempt in range(1, RETRIES + 1):
        try:
            with session.get(url, stream=True, timeout=TIMEOUT_S) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1 << 20):
                        f.write(chunk)
            size = dest.stat().st_size
            if size < MIN_EXPECTED_BYTES:
                raise OSError(f"suspiciously small download ({size} bytes)")
            return "ok"
        except BaseException as e:  # includes KeyboardInterrupt: never leave a partial file
            dest.unlink(missing_ok=True)
            if isinstance(e, KeyboardInterrupt):
                raise
            print(f"  attempt {attempt}/{RETRIES} failed: {e}", file=sys.stderr)
            if attempt < RETRIES:
                time.sleep(BACKOFF_S * attempt)
    return "fail"


def parse_months(spec: str) -> list[int]:
    """'1-6' -> [1..6]; '1,3,5' -> [1,3,5]; default '1-12'."""
    if "-" in spec:
        lo, hi = spec.split("-", 1)
        return list(range(int(lo), int(hi) + 1))
    return [int(m) for m in spec.split(",")]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", type=int, default=2015, help="first year (default 2015)")
    ap.add_argument("--end", type=int, default=2019, help="last year, inclusive (default 2019)")
    ap.add_argument("--months", default="1-12", help="months per year, e.g. '1-6' (default 1-12)")
    args = ap.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    months = parse_months(args.months)
    jobs = [(y, m) for y in range(args.start, args.end + 1) for m in months]

    counts = {"ok": 0, "skip": 0, "fail": 0}
    failed: list[tuple[int, int]] = []
    with requests.Session() as session:
        session.headers["User-Agent"] = "flight-delay-analysis research downloader"
        for i, (year, month) in enumerate(jobs, 1):
            print(f"[{i}/{len(jobs)}] {year}-{month:02d} ...", flush=True)
            status = download_month(session, year, month)
            counts[status] += 1
            if status == "fail":
                failed.append((year, month))

    print(f"\ndone: {counts['ok']} downloaded, {counts['skip']} skipped, {counts['fail']} failed")
    if failed:
        print("failed months (re-run to retry):", ", ".join(f"{y}-{m:02d}" for y, m in failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
