"""Sprint 2, task 2.1: test the gold price source.

Downloads the daily history of gold futures (Yahoo Finance ticker GC=F) and
checks whether it is good enough to build on:
  1. How far back does it go, and how many days are there?
  2. Are there missing stretches?
  3. Are there suspicious one-day jumps (often a sign of a futures contract "roll")?

Run from the project root:  python src/test_gold_source.py
"""

from pathlib import Path

import pandas as pd

TICKER = "GC=F"
START = "2000-01-01"
GAP_DAYS = 5        # a break longer than this many calendar days counts as a gap
JUMP_PCT = 5.0      # a one-day move bigger than this (in %) gets flagged


def analyze(prices: pd.DataFrame) -> dict:
    """Return simple quality facts about a table with a 'Close' column and a date index."""
    close = prices["Close"].dropna()
    close = close[close > 0]
    dates = close.index

    gaps = pd.Series(dates[1:] - dates[:-1], index=dates[1:])
    long_gaps = gaps[gaps > pd.Timedelta(days=GAP_DAYS)]

    moves = close.pct_change().dropna() * 100
    big_moves = moves[moves.abs() > JUMP_PCT]
    top_moves = moves.reindex(moves.abs().sort_values(ascending=False).index).head(5)

    return {
        "first_date": dates.min(),
        "last_date": dates.max(),
        "rows": len(close),
        "long_gaps": long_gaps,
        "big_moves": big_moves,
        "top_moves": top_moves,
    }


def main() -> int:
    import yfinance as yf  # imported here so the checks above can be tested without it

    prices = yf.Ticker(TICKER).history(start=START, auto_adjust=False)
    if prices.empty:
        print(f"No data came back for {TICKER}. Check your internet connection and try again.")
        return 1

    prices.index = prices.index.tz_localize(None).normalize()
    result = analyze(prices)

    print(f"Source: Yahoo Finance, ticker {TICKER} (gold futures, daily)")
    print(f"First date: {result['first_date'].date()}   Last date: {result['last_date'].date()}")
    print(f"Trading days: {result['rows']}")

    print(f"\nGaps longer than {GAP_DAYS} days: {len(result['long_gaps'])}")
    for date, gap in result["long_gaps"].head(5).items():
        print(f"  {gap.days} days ending {date.date()}")

    print(f"\nOne-day moves bigger than {JUMP_PCT:.0f}%: {len(result['big_moves'])}")
    print("Five largest one-day moves (check these dates for contract-roll jumps):")
    for date, pct in result["top_moves"].items():
        print(f"  {date.date()}: {pct:+.2f}%")

    out = Path("data/raw")
    out.mkdir(parents=True, exist_ok=True)
    prices[["Open", "High", "Low", "Close", "Volume"]].to_csv(out / "gold_gcf_test.csv")
    print(f"\nSaved a copy to {out / 'gold_gcf_test.csv'} (this folder is not committed to GitHub).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
