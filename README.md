# Employee Attendance & Analytics API

FastAPI + MongoDB (6.0+). All application code is in `app/main.py`.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export MONGO_URI="mongodb://localhost:27017" MONGO_DB="attendance_db"   # a local .env also works; real env vars win
uvicorn app.main:app --port 8000
```
Indexes are created at startup (idempotent). Then open:
- http://localhost:8000/ - small dashboard (analytics, punch in/out, records, corrections, employees)
- http://localhost:8000/docs - Swagger UI

MongoDB quickly: `docker run -p 27017:27017 mongo:7`. Demo data: `python seed_demo.py` (awkward cases) or
`python seed_demo.py --bulk` (about 100k records for index checks). It replaces both collections, so use a scratch DB.

## Tests
`pip install -r requirements-dev.txt`
- `pytest tests/test_rules.py` - rules R1-R5, R8 as pure functions
- `MONGO_DB=attendance_test pytest` - everything against a real MongoDB (CRUD, concurrency, analytics, explain)
- `ATTENDANCE_TEST_MOCK=1 pytest` - CRUD tests on mongomock without a database (aggregation tests skipped)

## Status / things to know
- All endpoints of the contract are implemented, including `/admin/explain/{endpoint}`.
- The aggregation pipelines (`$lookup`, `$setWindowFields`, `$densify`, `$unionWith`/`$documents`) need MongoDB 6.0+.
- **Honest note:** I could not run a real MongoDB where the code was written, so the pipelines and explain
  plans were reviewed by hand but not executed. The tests in `tests/test_api.py` marked as needing MongoDB are the
  first thing to run.
- Ambiguities I resolved: the trend range limit is 92 calendar days inclusive; the 7-day moving average averages the
  unrounded daily rates and rounds the result; a PATCH with an explicit `null` is a 422 (omit a field to leave it).
- Review of the starter code: `REVIEW.md`. Design answers: `DECISIONS.md`.
