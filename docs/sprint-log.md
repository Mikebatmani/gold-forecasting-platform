# Sprint Log

One entry per sprint: goal, result, and what we change. A dated record of how the project was run.

## Sprint 1: Set up (planned Oct 9-11, 2026; running to Oct 25)

- **Goal:** Repo with a first commit, working FRED key, 1-page plan saved, list of letter writers.
- **Decisions:** daily data, 63-trading-day-ahead direction target, one decision per quarter (confirmed Oct 12, 2026).
- **Scope:** unchanged. No task has been removed.

### Progress

| Date | Done | Next |
|---|---|---|
| Oct 8, 2026 | GitHub repository created. Agile Scrum chosen. | Design and first commit. |
| Oct 12, 2026 | Design confirmed. Project charter saved. Starter files created and first commit pushed. | FRED key and connection check. |
| Oct 13, 2026 | FRED API key working; connection check passes. | Test the gold price source. |
| Oct 15, 2026 | Gold source test passed (Yahoo GC=F): 6,557 trading days from Aug 30, 2000 to Oct 15, 2026, no gaps over 5 days, 22 one-day moves over 5%. The five largest moves match real market events. New access token in use. README status updated. | Check roll jumps against a gold ETF; collect the market series. |
| Oct 20, 2026 | Reviewed candidate metrics and which data fits gold's history. FRED start dates checked: real yield Jan 2, 2003; Fed broad dollar index Jan 2, 2006; gold volatility Jun 3, 2008; FRED S&P 500 holds only 10 years. | Collect the market series (task 2.2). |
| Oct 25, 2026 | Sprint log brought up to date. | Sprint 2: collect data. |

### Findings so far

- Real-yield data starts in 2003, so the main sample will likely start in January 2003 (about 94 independent quarters instead of about 104).
- Dollar index and S&P 500 history will come from Yahoo; the Fed broad dollar index and gold volatility are robustness checks.
- Gold futures are not spot gold. A roll-jump check against a gold ETF is still open.

### What we change

The first sprints ran about two weeks past their planned dates. The scope is unchanged. Weekly hours rise later in the plan, so the remaining work keeps its full scope and the dates move.

## Sprint 2: Data sources (started Oct 25, 2026)

- **Goal:** Clean daily gold data plus the market series, with monthly numbers stored by release date.
- **Scope:** unchanged. No task has been removed.

### Progress

| Date | Done | Next |
|---|---|---|
| Oct 25, 2026 | Task 2.2: 20 market series downloaded and checked (commit 52bab0b). Task 2.3: CPI, M2 and unemployment saved with first-release dates, 320 months each since 2000, no bad dates (commit 7757de3). | Task 2.4: join everything by release date into one table. |

### Findings so far

- Typical release delay: CPI about 45 days, M2 about 43, unemployment about 34.
- October 2025 is missing for CPI and unemployment (probably the 2025 government shutdown; to be verified). The table build must carry the last known value forward and mark it stale.
