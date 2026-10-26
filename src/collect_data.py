"""Sprint 2, task 2.2: collect the market series.

Downloads daily market series from FRED and Yahoo Finance, saves each one as a
CSV in data/raw/, and prints a check table: how many rows, first and last date,
and the longest gap. This also confirms that each FRED series ID is real.

Run from the project root:  python src/collect_data.py

Security notes:
  * The FRED key is read from the local .env file and is never printed.
  * Error messages are cut down to the error type and HTTP status, because a
    full network error message can contain the web address, which holds the key.
  * Files are written only inside data/raw/.
"""

import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

FRED_BASE = "https://api.stlouisfed.org/fred"
RAW_DIR = Path("data/raw")
GAP_DAYS = 5  # a break longer than this many calendar days is flagged
WEEKLY_SERIES = {"WALCL"}  # weekly series: a 7-day step is normal
WEEKLY_GAP_DAYS = 10

# Series the plan needs for Sprint 2 (task 2.2). Saved to data/raw/.
FRED_REQUIRED = {
    "DGS10": "10-year Treasury yield",
    "DFII10": "10-year real yield (TIPS)",
    "T10YIE": "10-year expected inflation (breakeven)",
    "VIXCLS": "VIX, stock market fear gauge",
    "DTWEXBGS": "Fed broad US dollar index",
}

# Candidates for later sprints. Saved too, so their IDs and start dates are verified.
FRED_CANDIDATES = {
    "DFF": "Fed funds rate",
    "T10Y2Y": "10-year minus 2-year yield",
    "GVZCLS": "Gold volatility index (GVZ)",
    "WALCL": "Fed balance sheet (weekly)",
    "DEXUSEU": "US dollars per euro",
    "DEXJPUS": "Japanese yen per US dollar",
    "DCOILBRENTEU": "Brent oil price",
}

# Monthly series: only their details are checked here. Their values are NOT saved
# yet, because monthly data must be stored with release dates (task 2.3).
FRED_INFO_ONLY = {
    "CPIAUCNS": "CPI, not seasonally adjusted (monthly)",
    "M2SL": "M2 money supply (monthly)",
    "UNRATE": "Unemployment rate (monthly)",
}

YAHOO = {
    "GC=F": "Gold futures",
    "DX-Y.NYB": "US dollar index (DXY)",
    "^GSPC": "S&P 500",
    "GLD": "Gold ETF (for the roll-jump check)",
    "GDX": "Gold miners ETF (Sprint 7)",
}


class FredError(Exception):
    """A FRED request failed. Carries only the HTTP status, never the web address."""

    def __init__(self, status: Optional[int]):
        super().__init__(f"HTTP {status}" if status else "no response")
        self.status = status


def safe_error(exc: Exception) -> str:
    """Describe an error without leaking the request web address (it holds the key)."""
    if isinstance(exc, FredError):
        return f"FRED error ({exc})"
    status = getattr(getattr(exc, "response", None), "status_code", None)
    return type(exc).__name__ + (f" (HTTP {status})" if status else "")


def file_stem(ticker: str) -> str:
    """Turn a Yahoo ticker such as ^GSPC or GC=F into a safe file name part."""
    return re.sub(r"[^A-Za-z0-9]+", "", ticker)


def parse_observations(payload: dict) -> pd.Series:
    """Turn FRED's JSON into a number series indexed by date.

    FRED writes "." for a day with no value (for example a bank holiday); that
    becomes a missing number, not a zero.
    """
    rows = payload.get("observations", [])
    dates = pd.to_datetime([r["date"] for r in rows])
    values = pd.to_numeric([r["value"] for r in rows], errors="coerce")
    return pd.Series(values, index=pd.DatetimeIndex(dates, name="date"), dtype="float64")


def summarize(series: pd.Series) -> Dict[str, object]:
    """Quality facts about a series: first and last real value, rows, gaps."""
    valid = series.dropna()
    if valid.empty:
        return {"rows": 0, "missing": int(len(series)), "first": None, "last": None, "longest_gap": None}
    dates = valid.index
    gaps = pd.Series(dates[1:] - dates[:-1]) if len(dates) > 1 else pd.Series([], dtype="timedelta64[ns]")
    longest = int(gaps.max().days) if len(gaps) else 0
    return {
        "rows": int(len(valid)),
        "missing": int(series.isna().sum()),
        "first": dates.min().date(),
        "last": dates.max().date(),
        "longest_gap": longest,
    }


def fred_get(path: str, params: dict, api_key: str) -> dict:
    """One FRED request with a short retry. Never puts the key in an error message."""
    query = dict(params, api_key=api_key, file_type="json")
    last_status = None
    for attempt in range(3):
        try:
            response = requests.get(FRED_BASE + path, params=query, timeout=30)
        except requests.RequestException:
            last_status = None
            time.sleep(2 * (attempt + 1))
            continue
        last_status = response.status_code
        if response.status_code == 200:
            return response.json()
        if response.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 * (attempt + 1))
            continue
        break  # for example 400 = unknown series ID: retrying will not help
    raise FredError(last_status)


def fetch_fred_info(series_id: str, api_key: str) -> dict:
    """Title, frequency and date range as FRED states them."""
    payload = fred_get("/series", {"series_id": series_id}, api_key)
    info = payload["seriess"][0]
    return {
        "title": info.get("title", ""),
        "frequency": info.get("frequency_short", "?"),
        "start": info.get("observation_start", "?"),
        "end": info.get("observation_end", "?"),
    }


def fetch_fred_series(series_id: str, api_key: str) -> pd.Series:
    payload = fred_get("/series/observations", {"series_id": series_id}, api_key)
    return parse_observations(payload)


def fetch_yahoo(ticker: str) -> pd.DataFrame:
    import yfinance as yf  # imported here so the checks above run without it

    prices = yf.Ticker(ticker).history(period="max", auto_adjust=False)
    if prices.empty:
        raise ValueError("no data returned")
    index = prices.index
    if getattr(index, "tz", None) is not None:
        index = index.tz_localize(None)
    prices.index = pd.DatetimeIndex(index.normalize(), name="date")
    return prices[["Open", "High", "Low", "Close", "Volume"]]


def save_csv(frame, name: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    frame.to_csv(path)
    return path


def print_row(source: str, ident: str, label: str, facts: Dict[str, object], note: str = "") -> None:
    gap = facts["longest_gap"]
    limit = WEEKLY_GAP_DAYS if ident in WEEKLY_SERIES else GAP_DAYS
    flag = " <- long gap" if isinstance(gap, int) and gap > limit else ""
    print(
        f"{source:<6} {ident:<13} {label[:38]:<38} "
        f"{str(facts['rows']):>6}  {str(facts['first']):<10}  {str(facts['last']):<10}  "
        f"{str(gap):>5}{flag}{note}"
    )


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv()  # reads FRED_API_KEY from the local .env file
    api_key = os.getenv("FRED_API_KEY")
    if not api_key or api_key == "your_key_here":
        print("FRED_API_KEY is missing. Copy .env.example to .env and add your key.")
        return 1

    print(f"{'Source':<6} {'ID':<13} {'What':<38} {'Rows':>6}  {'First':<10}  {'Last':<10}  {'Gap d':>5}")
    print("-" * 100)
    failures_required: List[str] = []
    failures_other: List[str] = []

    for group, required in ((FRED_REQUIRED, True), (FRED_CANDIDATES, False)):
        for series_id, label in group.items():
            try:
                series = fetch_fred_series(series_id, api_key)
                save_csv(series.rename("value"), f"fred_{series_id}.csv")
                print_row("FRED", series_id, label, summarize(series))
            except Exception as exc:  # report the type only, never the message
                print(f"FRED   {series_id:<13} {label[:38]:<38} FAILED: {safe_error(exc)}")
                (failures_required if required else failures_other).append(series_id)
            time.sleep(0.5)  # stay well under FRED's rate limit

    for series_id, label in FRED_INFO_ONLY.items():
        try:
            info = fetch_fred_info(series_id, api_key)
            print(f"{'info':<6} {series_id:<13} {label[:38]:<38} {'':>6}  {info['start']:<10}  {info['end']:<10}  "
                  f"{info['frequency']:>5}  (frequency; values saved in task 2.3)")
        except Exception as exc:
            print(f"info   {series_id:<13} {label[:38]:<38} FAILED: {safe_error(exc)}")
            failures_other.append(series_id)
        time.sleep(0.5)

    for ticker, label in YAHOO.items():
        required = ticker in ("GC=F", "DX-Y.NYB", "^GSPC")
        try:
            prices = fetch_yahoo(ticker)
            save_csv(prices, f"yahoo_{file_stem(ticker)}.csv")
            print_row("Yahoo", ticker, label, summarize(prices["Close"]))
        except Exception as exc:
            print(f"Yahoo  {ticker:<13} {label[:38]:<38} FAILED: {safe_error(exc)}")
            (failures_required if required else failures_other).append(ticker)

    print("-" * 100)
    print(f"Saved copies are in {RAW_DIR}/ (this folder is not committed to GitHub).")
    if failures_required:
        print("Needed series that failed: " + ", ".join(failures_required))
    if failures_other:
        print("Optional series that failed: " + ", ".join(failures_other))
    if not failures_required and not failures_other:
        print("All series downloaded.")
    return 1 if failures_required else 0


if __name__ == "__main__":
    sys.exit(main())
