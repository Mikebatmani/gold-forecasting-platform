"""Checks for src/collect_releases.py that need no internet and no API key.

Run from the project root:  python tests/test_collect_releases.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import collect_releases as cr  # noqa: E402


def make_payload():
    return {"observations": [
        {"date": "2024-02-01", "realtime_start": "2024-03-12", "value": "310.0"},
        {"date": "2024-01-01", "realtime_start": "2024-02-13", "value": "309.5"},
        {"date": "2024-03-01", "realtime_start": "2024-04-10", "value": "."},
    ]}


def test_missing_value_is_dropped_not_zero():
    frame = cr.parse_releases(make_payload())
    assert len(frame) == 2
    assert (frame["value"] > 0).all()


def test_release_date_and_lag_are_kept_and_sorted():
    frame = cr.parse_releases(make_payload())
    assert str(frame["release_date"].iloc[0].date()) == "2024-02-13"   # sorted by release
    assert str(frame["reference_period"].iloc[0].date()) == "2024-01-01"
    assert int(frame["lag_days"].iloc[0]) == 43                         # Jan 1 to Feb 13


def test_good_data_passes_the_checks():
    facts = cr.check_releases(cr.parse_releases(make_payload()))
    assert facts["rows"] == 2
    assert facts["bad_lag"] == 0 and facts["duplicates"] == 0 and facts["out_of_order"] == 0
    assert facts["median_lag"] == 41   # lags are 43 and 40 days; the middle is 41.5


def test_release_before_its_month_is_flagged():
    payload = {"observations": [
        {"date": "2024-05-01", "realtime_start": "2024-04-20", "value": "1.0"},  # impossible: released early
    ]}
    facts = cr.check_releases(cr.parse_releases(payload))
    assert facts["bad_lag"] == 1


def test_very_late_release_is_flagged():
    payload = {"observations": [
        {"date": "2020-01-01", "realtime_start": "2021-01-01", "value": "1.0"},
    ]}
    assert cr.check_releases(cr.parse_releases(payload))["bad_lag"] == 1


def test_duplicate_month_and_wrong_order_are_flagged():
    payload = {"observations": [
        {"date": "2024-01-01", "realtime_start": "2024-02-13", "value": "1.0"},
        {"date": "2024-01-01", "realtime_start": "2024-02-14", "value": "1.1"},
        {"date": "2024-02-01", "realtime_start": "2024-02-10", "value": "2.0"},  # Feb released before Jan
    ]}
    facts = cr.check_releases(cr.parse_releases(payload))
    assert facts["duplicates"] == 1
    assert facts["out_of_order"] >= 1


def test_empty_payload_does_not_crash():
    facts = cr.check_releases(cr.parse_releases({"observations": []}))
    assert facts["rows"] == 0 and facts["first_ref"] is None


def test_error_text_never_contains_the_key():
    secret = "SECRETKEY123"

    class Leaky(Exception):
        pass

    assert secret not in cr.safe_error(Leaky(f"Max retries exceeded with url: /fred?api_key={secret}"))


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"{len(tests)} checks passed.")
