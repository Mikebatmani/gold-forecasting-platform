"""Checks for src/collect_data.py that need no internet and no API key.

Run from the project root:  python tests/test_collect_data.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import collect_data as cd  # noqa: E402


def test_dot_becomes_missing_not_zero():
    payload = {"observations": [
        {"date": "2024-01-01", "value": "."},
        {"date": "2024-01-02", "value": "4.25"},
    ]}
    series = cd.parse_observations(payload)
    assert pd.isna(series.iloc[0])
    assert series.iloc[1] == 4.25


def test_summary_counts_rows_missing_and_longest_gap():
    index = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-15", "2024-01-16"])
    series = pd.Series([1.0, 2.0, None, 4.0, 5.0], index=index)
    facts = cd.summarize(series)
    assert facts["rows"] == 4          # the None is not counted as a row of data
    assert facts["missing"] == 1
    assert str(facts["first"]) == "2024-01-02"
    assert str(facts["last"]) == "2024-01-16"
    assert facts["longest_gap"] == 12  # Jan 3 to Jan 15


def test_summary_of_empty_series_does_not_crash():
    facts = cd.summarize(pd.Series([None, None], index=pd.to_datetime(["2024-01-01", "2024-01-02"])))
    assert facts["rows"] == 0 and facts["first"] is None


def test_error_text_never_contains_the_key():
    secret = "SECRETKEY123"

    class Leaky(Exception):
        pass

    message = f"Max retries exceeded with url: /fred/series?api_key={secret}"
    assert secret not in cd.safe_error(Leaky(message))
    assert secret not in cd.safe_error(cd.FredError(400))


def test_file_names_are_safe():
    assert cd.file_stem("^GSPC") == "GSPC"
    assert cd.file_stem("GC=F") == "GCF"
    assert cd.file_stem("DX-Y.NYB") == "DXYNYB"


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"{len(tests)} checks passed.")
