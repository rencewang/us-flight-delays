"""Convert downloaded BTS monthly zips to typed, column-pruned Parquet.

Each zip contains one CSV with 100+ columns; we keep ~33. Times (CRSDepTime etc.)
are kept as zero-padded strings ("0700") — parsing to timestamps happens at the
feature stage, together with the timezone conversion, so this layer stays dumb.

Idempotent: skip existing parquet files.

Usage:
    uv run python src/ingest/bts_to_parquet.py            # convert everything in data/raw/
    uv run python src/ingest/bts_to_parquet.py --force    # reconvert all
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import polars as pl

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PARQUET_DIR = Path(__file__).resolve().parents[2] / "data" / "parquet"
PREFIX = "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_"

# Column subset (~33 of 100+). Names as they appear in the PREZIP CSV header.
KEEP: dict[str, pl.DataType] = {
    # identity / calendar
    "Year": pl.Int16,
    "Month": pl.Int8,
    "DayofMonth": pl.Int8,
    "DayOfWeek": pl.Int8,
    "FlightDate": pl.Utf8,  # cast to Date after read
    "Reporting_Airline": pl.Utf8,
    "Tail_Number": pl.Utf8,
    "Flight_Number_Reporting_Airline": pl.Utf8,
    "Origin": pl.Utf8,
    "Dest": pl.Utf8,
    # departure
    "CRSDepTime": pl.Utf8,  # "0700"-style local times; keep leading zeros
    "DepTime": pl.Utf8,
    "DepDelayMinutes": pl.Float64,
    "DepDel15": pl.Float64,
    "TaxiOut": pl.Float64,
    "WheelsOff": pl.Utf8,
    # arrival
    "WheelsOn": pl.Utf8,
    "TaxiIn": pl.Float64,
    "CRSArrTime": pl.Utf8,
    "ArrTime": pl.Utf8,
    "ArrDelayMinutes": pl.Float64,
    "ArrDel15": pl.Float64,
    # status
    "Cancelled": pl.Float64,
    "CancellationCode": pl.Utf8,
    "Diverted": pl.Float64,
    # durations / distance
    "CRSElapsedTime": pl.Float64,
    "ActualElapsedTime": pl.Float64,
    "Distance": pl.Float64,
    # delay cause attribution (only populated when ArrDel15 == 1)
    "CarrierDelay": pl.Float64,
    "WeatherDelay": pl.Float64,
    "NASDelay": pl.Float64,
    "SecurityDelay": pl.Float64,
    "LateAircraftDelay": pl.Float64,
}


def convert(zip_path: Path, force: bool = False) -> str:
    out = PARQUET_DIR / f"bts_{zip_path.stem.removeprefix(PREFIX)}.parquet"
    if out.exists() and not force:
        return "skip"

    with zipfile.ZipFile(zip_path) as zf:
        csv_name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        df = pl.read_csv(
            zf.read(csv_name),
            columns=list(KEEP.keys()),
            schema_overrides=KEEP,
            # BTS rows end with a trailing comma (a phantom empty last column);
            # selecting explicit columns sidesteps it.
        )

    df = df.with_columns(
        pl.col("FlightDate").str.to_date("%Y-%m-%d"),
        pl.col("Cancelled").cast(pl.Int8),
        pl.col("Diverted").cast(pl.Int8),
        pl.col("DepDel15").cast(pl.Int8),
        pl.col("ArrDel15").cast(pl.Int8),
        # Empty-string tail numbers -> null, so null-rate stats mean one thing
        pl.when(pl.col("Tail_Number") == "")
        .then(None)
        .otherwise(pl.col("Tail_Number"))
        .alias("Tail_Number"),
    )
    df.write_parquet(out, compression="zstd")
    return "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="reconvert even if parquet exists")
    args = ap.parse_args()

    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    zips = sorted(RAW_DIR.glob(f"{PREFIX}*.zip"))
    if not zips:
        print(f"no zips found in {RAW_DIR} — run download_bts.py first", file=sys.stderr)
        return 1

    counts = {"ok": 0, "skip": 0, "fail": 0}
    for i, zp in enumerate(zips, 1):
        try:
            status = convert(zp, force=args.force)
        except Exception as e:
            print(f"[{i}/{len(zips)}] {zp.name} FAILED: {e}", file=sys.stderr)
            counts["fail"] += 1
            continue
        counts[status] += 1
        if status == "ok":
            print(f"[{i}/{len(zips)}] {zp.name} -> parquet", flush=True)

    print(f"\ndone: {counts['ok']} converted, {counts['skip']} skipped, {counts['fail']} failed")
    return 1 if counts["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
