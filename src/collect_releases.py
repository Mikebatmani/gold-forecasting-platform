"""Sprint 2, task 2.3: monthly series saved WITH their release dates.

A monthly number such as "CPI for September" is not known on September 1. It is
published weeks later. If the model sees it on the wrong day, it "knows the
future" (lookahead bias). So for each monthly series this script saves, for
every month:

    reference_period  the month the number describes
    release_date      the first day the public could see it
    value             the number as first published (later revisions ignored)
    lag_days          release_date minus reference_period

The values come from FRED's vintage archive (called ALFRED), asking for the
"initial release only" view.

Run from the project root:  python src/collect_releases.py

Security notes (same rules as collect_data.py):
  * The FRED key is read from the local .env file and is never printed.
  * Error messages show only the error type and HTTP status.
  * Files are written only inside data/raw/.
"""

import os
import sys
import time
from typing import Dict, List

import pandas as pd

from collect_data import RAW_DIR, FredError, fred_get, safe_error, save_csv  # noqa: F401

SERIES = {
    "CPIAUCNS": "CPI, not seasonally adjusted",
    "M2SL": "M2 money supply",
    "UNRATE": "Unemployment rate",
}

START = "2000-01-01"          # reference periods before this are not needed
MIN_LAG_DAYS = 1              # a release on or before its own month's first day is impossible
MAX_LAG_DAYS = 120            # a lag this long means a data problem or a very late first release


def parse_releases(payload: dict) -> pd.DataFrame:
    """Turn FRED's "initial release" JSON into a table of release facts.

    FRED writes "." when a value is missing; that row is dropped, not turned
    into a zero. Rows are sorted by release date.
    """
    rows = payload.get("observations", [])
    frame = pd.DataFrame(
        {
            "reference_period": pd.to_datetime([r["date"] for r in rows]),
            "release_date": pd.to_datetime([r["realtime_start"] for r in rows]),
            "value": pd.to_numeric([r["value"] for r in rows], errors="coerce"),
        }
    )
    frame = frame.dropna(subset=["value"]).sort_values("release_date").reset_index(drop=True)
    frame["lag_days"] = (frame["release_date"] - frame["reference_period"]).dt.days
    return frame


def check_releases(frame: pd.DataFrame) -> Dict[str, object]:
    """Quality facts: rows, dates, typical lag, and rows that look wrong."""
    if frame.empty:
        return {"rows": 0, "first_ref": None, "last_ref": None, "first_release": None,
                "median_lag": None, "bad_lag": 0, "duplicates": 0, "out_of_order": 0}
    bad_lag = int(((frame["lag_days"] < MIN_LAG_DAYS) | (frame["lag_days"] > MAX_LAG_DAYS)).sum())
    duplicates = int(frame["reference_period"].duplicated().sum())
    # months should be released in the same order as they happen
    ordered = frame.sort_values("reference_period")
    out_of_order = int((ordered["release_date"].diff().dt.days < 0).sum())
    return {
        "rows": int(len(frame)),
        "first_ref": frame["reference_period"].min().date(),
        "last_ref": frame["reference_period"].max().date(),
        "first_release": frame["release_date"].min().date(),
        "median_lag": int(frame["lag_days"].median()),
        "bad_lag": bad_lag,
        "duplicates": duplicates,
        "out_of_order": out_of_order,
    }


def fetch_releases(series_id: str, api_key: str) -> pd.DataFrame:
    """First-published value and release date for every month, via FRED vintages."""
    payload = fred_get(
        "/series/observations",
        {
            "series_id": series_id,
            "output_type": 4,                    # 4 = initial release only
            "realtime_start": "1776-07-04",      # ask for the whole vintage archive
            "realtime_end": "9999-12-31",
            "observation_start": START,
        },
        api_key,
    )
    return parse_releases(payload)


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("FRED_API_KEY")
    if not api_key or api_key == "your_key_here":
        print("FRED_API_KEY is missing. Copy .env.example to .env and add your key.")
        return 1

    head = (f"{'ID':<9} {'Rows':>5}  {'First month':<11} {'Last month':<11} {'First release':<13} "
            f"{'Median lag':>10} {'Bad lag':>7} {'Dupes':>5} {'Order':>5}")
    print(head)
    print("-" * len(head))
    failed: List[str] = []
    for series_id, label in SERIES.items():
        try:
            frame = fetch_releases(series_id, api_key)
            facts = check_releases(frame)
            save_csv(frame.set_index("reference_period"), f"releases_{series_id}.csv")
            print(f"{series_id:<9} {facts['rows']:>5}  {str(facts['first_ref']):<11} {str(facts['last_ref']):<11} "
                  f"{str(facts['first_release']):<13} {str(facts['median_lag']):>8} d {facts['bad_lag']:>7} "
                  f"{facts['duplicates']:>5} {facts['out_of_order']:>5}")
        except Exception as exc:  # type only, never the message
            print(f"{series_id:<9} FAILED: {safe_error(exc)}")
            failed.append(series_id)
        time.sleep(0.5)
    print("-" * len(head))
    print(f"Saved copies are in {RAW_DIR}/ (not committed to GitHub).")
    print("Bad lag = a release before its month began, or more than "
          f"{MAX_LAG_DAYS} days after. Dupes and Order should be 0.")
    if failed:
        print("Failed: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
