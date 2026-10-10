# REVIEW.md

Defects found in the starter `app/main.py`. All are fixed in this submission.

| # | Where | What is wrong | How you'd notice it | How I fixed it |
|---|---|---|---|---|
| 1 | `compute_late_minutes` | Uses `punch_in.replace(hour, minute)` on whatever time zone the datetime has (naive/UTC/local), not IST, and anchors to the datetime's own calendar day. | Punch in at 09:50 IST: the UTC date and time make "shift start" 09:30 UTC, so the result is wrong by 5.5 h. | Shift start is built from the attendance date at the IST wall-clock time (`_at`). |
| 2 | `compute_late_minutes` | `int(seconds/60) > 10` instead of "strictly more than 10:00": 09:40:01 gives 10 min, which is `> 10` false, so 0 (should be 10); seconds are not truncated first. | Punch in 09:40:01 -> expects 10, gets 0. | Compare seconds `> 600`, then floor to minutes (R2). Instants are truncated on input. |
| 3 | `compute_late_minutes` / `punch_in` | No overnight-shift handling: a 00:30 punch-in of a 22:00-06:00 shift gets the wrong date and a negative or absent lateness. | Overnight employee punches in after midnight. | `attendance_date()` implements R1; late/overtime are anchored on that date. |
| 4 | `compute_work_hours` | Python `round()` is banker's/float rounding, not half-up (R4); sub-second parts leak in. | 4.125 h -> 4.12 instead of 4.13. | `Decimal` with `ROUND_HALF_UP` on whole seconds. |
| 5 | `compute_overtime` | No 30-minute minimum (R3); builds the end time with `fromisoformat(date_str).replace(tzinfo=IST)` but `punch_out` may be naive (TypeError); overnight shifts end the next day, not the same day. | Punch out 18:35 gives 5 min overtime, should be 0. | Rewritten: floor to minutes, count only when `>= 30`, end moves to the next day for overnight shifts. |
| 6 | `create_employee` | Check-then-insert race, no unique index: parallel creates produce duplicates, no 409 for the loser. | 10 parallel POSTs with the same `emp_code`. | Unique index on `emp_code`; catch `DuplicateKeyError` -> 409. |
| 7 | `create_employee` / `EmployeeIn` | No validation (code format, email, shift pattern, `shift_start == shift_end`, `joined_on` real date); `created_at` is naive local `datetime.now()` returned as an ISO string instead of epoch ms. | POST `joined_on: "2026-13-45"` returns 201. | Pydantic patterns + validator; `created_at` stored as UTC and returned as ms. |
| 8 | `list_employees` | `skip = page * page_size` skips the whole first page; `total` counts the entire collection, ignoring the filter; no sort, so pages are unstable; `page_size` unbounded, `page=0`/negatives give 500 or wrong data. | `GET /employees?page=1` returns page 2. | `skip = (page-1)*page_size`, `count_documents(filter)`, sort by `emp_code`, `Query(ge=1, le=100)`. |
| 9 | `punch_in` | Unknown employee: `emp` is `None` and `emp["shift_start"]` raises TypeError, so a 500. | Punch in with a bad `emp_code`. | `get_employee()` raises 404. |
| 10 | `punch_in` | Check-then-insert race: two simultaneous requests both pass `find_one` and both insert. | Parallel identical punch-ins give two 201s. | Unique `(emp_code, date)` index; `DuplicateKeyError` -> 409. |
| 11 | `punch_in` | `datetime.fromtimestamp(ms/1000)` uses the server's local zone and returns naive values; `date` is therefore the server's date, not IST (R1); `if body.punched_at` treats a falsy value as "missing"; no truncation to seconds. | Run on a UTC server, punch in at 00:10 IST. | `ms_to_dt` (UTC-aware, truncated), `attendance_date` (IST). |
| 12 | `PunchInIn` | `punched_at` accepts any int (seconds, negative), floats are coerced; `status` is any string, so ABSENT/LEAVE/garbage can be created. | `status: "FOO"`, `punched_at: 1783312500`. | `EpochMs` strict int in `[1e11, 4.1e12]`; `status` is a `Literal` of the three presence values -> 422. |
| 13 | `punch_in` response | Returns an `id` (the ObjectId) and raw datetimes; `_id` must never leave the API, instants must be epoch ms. | Look at the response body. | `record_out()` serialiser used by every endpoint. |
| 14 | `list_attendance` | Loads the whole collection into memory, sorts and pages in Python, no index: unusable at 100k records. | 100k documents, request latency and memory. | Server-side filter/sort/skip/limit with matching indexes and a hint. |
| 15 | `list_attendance` | Sort only by `date` (ties not by `emp_code` asc); `page`/`page_size` unvalidated (`page=0` slices negatively); `date_from > date_to`, invalid dates and invalid `status` are accepted; response leaks `id`, datetimes and ignores legacy gaps (`history`, `half_day`). | `?page=0`, `?date_from=garbage`. | Sort `(date desc, emp_code asc)`, `Query` bounds, 422 on bad dates/range/status, `record_out`. |
| 16 | `/health` | Always returns ok, even with MongoDB down. | Stop MongoDB, call `/health`. | Pings MongoDB; 503 on failure. |
| 17 | `MongoClient(...)` | Naive datetimes (`tz_aware` off): arithmetic mixes naive and aware values (TypeError) and depends on server zone. | Any subtraction with an aware value. | `tz_aware=True`; `aware()` guard for safety. |
| 18 | whole file | No indexes at all; a PyMongo error anywhere becomes a 500. | `explain()` shows COLLSCAN. | Idempotent index creation at startup; `PyMongoError` handler returns 503. |

## Looked at and decided it was fine
- `load_dotenv()` with the default `override=False`: real environment variables already win, as required.
- `IST = timezone(timedelta(hours=5, minutes=30))`: correct, IST has no DST.
- Plain `def` endpoints with a synchronous PyMongo client: FastAPI runs them in a thread pool and `MongoClient` is thread-safe, so concurrency is fine.
- Extra fields on request bodies (for example a client sending `late_minutes`) are ignored by Pydantic's default, which is what the contract asks.
