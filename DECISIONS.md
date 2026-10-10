# DECISIONS.md

1. **Indexes.** `employees`: unique `emp_code`; `(department, emp_code)` for the sorted list; `(department, joined_on)` and `(joined_on)` for headcount. `attendance_logs`: unique `(emp_code, date)` (one record per day, the race guard, and every per-employee lookup); `(date desc, emp_code)` for the default list order and month scans; `(status, date desc, emp_code)` for status filters; `(emp_code, punch_in desc)` for punch-out. I rejected a partial index on `late_minutes > 0` for the leaderboard: it only helps one endpoint and adds write cost.
2. **Punch-in race.** Both requests find the employee, compute the same date and call `insert_one`. The unique `(emp_code, date)` index lets MongoDB accept one; the other gets `DuplicateKeyError`, which I turn into 409. No check-then-insert.
3. **Ties.** The pipeline ranks with `$rank` (1, 2, 2, 4) first and filters `rank <= limit` afterwards, so everyone tied at the cutoff is returned and the list can be longer than `limit`.
4. **Headcount.** The summary starts from `employees` (joined on or before month end) and `$lookup`s logs per employee. A person with no logs gets an empty array but is still counted once.
5. **At 100x data.** I would pre-aggregate monthly numbers per employee and department (updated on each write) instead of scanning raw logs on every request, and add pagination or caching to the analytics.
