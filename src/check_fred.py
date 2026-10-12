"""Sprint 1 check: confirm the FRED API key works.

Fetches the 5 most recent observations of the 10-year Treasury yield (DGS10)
and prints them. Run from the project root:  python src/check_fred.py
"""

import os
import sys

import requests
from dotenv import load_dotenv

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
SERIES_ID = "DGS10"  # 10-year Treasury constant maturity yield, daily


def main() -> int:
    load_dotenv()  # reads FRED_API_KEY from the local .env file
    api_key = os.getenv("FRED_API_KEY")
    if not api_key or api_key == "your_key_here":
        print("FRED_API_KEY is missing. Copy .env.example to .env and add your key.")
        return 1

    params = {
        "series_id": SERIES_ID,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 5,
    }
    response = requests.get(FRED_URL, params=params, timeout=30)
    if response.status_code != 200:
        print(f"FRED request failed with status {response.status_code}.")
        print(response.text[:300])
        return 1

    observations = response.json().get("observations", [])
    if not observations:
        print("The request worked but returned no observations.")
        return 1

    print(f"FRED key works. Latest {SERIES_ID} observations:")
    for obs in observations:
        # "." is how FRED marks a day with no value, such as a bank holiday.
        print(f"  {obs['date']}: {obs['value']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
