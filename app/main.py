"""
Employee Attendance & Analytics API  (FastAPI + MongoDB)

Run:   uvicorn app.main:app --port 8000
Env:   MONGO_URI, MONGO_DB  (a local .env is read for convenience; real environment variables win)
UI:    http://localhost:8000/        (small dashboard)   |   http://localhost:8000/docs   (Swagger)

Layout of this single file
    1. configuration, MongoDB client, indexes
    2. time / rounding helpers and the business rules R1-R5 (pure functions, unit-tested)
    3. request models and response serialisers
    4. employees, attendance (punch-in / punch-out / list / regularize)
    5. analytics: pipeline builders + endpoints (monthly, department summary, late leaderboard, trend)
    6. admin explain
    7. embedded dashboard UI
"""
import json
from app.ui import UI_HTML
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from datetime import date as Date
from datetime import datetime, time as TimeOfDay, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Any, Literal, Optional

from bson import json_util
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, model_validator
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

log = logging.getLogger("attendance")

# =========================================================================== #
# 1. Configuration, client, indexes
# =========================================================================== #
load_dotenv()  # override=False: variables already in the environment always win

# tz_aware=True: PyMongo hands back timezone-aware (UTC) datetimes instead of naive ones, so
# subtracting / converting them can never silently use the server's local time zone.
client = MongoClient(
    os.getenv("MONGO_URI") or "mongodb://localhost:27017",
    tz_aware=True,
    serverSelectionTimeoutMS=5000,
)
db = client[os.getenv("MONGO_DB") or "attendance_db"]
EMPLOYEES = "employees"
LOGS = "attendance_logs"

# (collection, keys, name, unique)
INDEXES = [
    # emp_code is the business key: uniqueness is enforced by the database, not by check-then-insert.
    (EMPLOYEES, [("emp_code", ASCENDING)], "uq_emp_code", True),
    # GET /employees?department=  (equality + sort by emp_code, no in-memory sort)
    (EMPLOYEES, [("department", ASCENDING), ("emp_code", ASCENDING)], "ix_dept_emp", False),
    # headcount (R9) and the department analytics: department equality + joined_on range
    (EMPLOYEES, [("department", ASCENDING), ("joined_on", ASCENDING)], "ix_dept_joined", False),
    # department summary without a department filter: joined_on range only
    (EMPLOYEES, [("joined_on", ASCENDING)], "ix_joined", False),
    # one record per (employee, day): punch-in race guard, regularize lookup, employee monthly, $lookups
    (LOGS, [("emp_code", ASCENDING), ("date", ASCENDING)], "uq_emp_date", True),
    # GET /attendance default order (date desc, emp_code asc) and date-range scans (leaderboard)
    (LOGS, [("date", DESCENDING), ("emp_code", ASCENDING)], "ix_date_emp", False),
    # GET /attendance?status=  filter + the same sort
    (LOGS, [("status", ASCENDING), ("date", DESCENDING), ("emp_code", ASCENDING)], "ix_status_date_emp", False),
    # punch-out: latest record of an employee whose punch_in <= punched_at
    (LOGS, [("emp_code", ASCENDING), ("punch_in", DESCENDING)], "ix_emp_punchin", False),
]
_indexes_ready = False


def ensure_indexes() -> bool:
    """Create all indexes; idempotent. A unique index that cannot be built (duplicate data) falls back to non-unique."""
    global _indexes_ready
    if _indexes_ready:
        return True
    try:
        for coll, keys, name, unique in INDEXES:
            try:
                db[coll].create_index(keys, name=name, unique=unique)
            except DuplicateKeyError:
                log.error("duplicate data prevents unique index %s; creating it non-unique", name)
                db[coll].create_index(keys, name=name)
        _indexes_ready = True
    except PyMongoError as exc:
        log.error("index creation failed: %s", exc)
    return _indexes_ready


@asynccontextmanager
async def lifespan(_: FastAPI):
    for _attempt in range(8):  # MongoDB may still be starting; the app must not crash because of that
        if ensure_indexes():
            break
        time.sleep(1)
    yield


app = FastAPI(title="Employee Attendance & Analytics API", version="2.0.0", lifespan=lifespan)


@app.exception_handler(PyMongoError)
async def mongo_error_handler(_: Request, exc: PyMongoError):
    log.error("MongoDB error: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "database unavailable"})


# =========================================================================== #
# 2. Helpers and business rules
# =========================================================================== #
IST = timezone(timedelta(hours=5, minutes=30))
UTC = timezone.utc
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
MS_MIN, MS_MAX = 100_000_000_000, 4_102_444_800_000

PRESENT_STATUSES = ["PRESENT", "WFH", "ON_DUTY"]  # R6
NON_PRESENT_STATUSES = ["ABSENT", "LEAVE"]
ALL_STATUSES = PRESENT_STATUSES + NON_PRESENT_STATUSES
StatusT = Literal["PRESENT", "ABSENT", "LEAVE", "WFH", "ON_DUTY"]

DATE_RE = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
MONTH_RE = r"^[0-9]{4}-(0[1-9]|1[0-2])$"
HHMM_RE = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"
GRACE_SECONDS = 10 * 60
MIN_OVERTIME_MINUTES = 30
HALF_DAY_HOURS = Decimal("4.50")


def unprocessable(msg: str, *loc: str) -> HTTPException:
    """422 with the same body shape FastAPI uses for validation errors."""
    return HTTPException(422, [{"type": "value_error", "loc": list(loc) or ["body"], "msg": msg}])


def ms_to_dt(ms: int) -> datetime:
    """Epoch milliseconds -> aware UTC datetime, truncated to whole seconds (R1)."""
    return (EPOCH + timedelta(milliseconds=ms)).replace(microsecond=0)


def now_utc() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)  # BSON dates are UTC
    return dt


def dt_to_ms(dt: Optional[datetime]) -> Optional[int]:
    dt = aware(dt)
    return None if dt is None else (dt - EPOCH) // timedelta(milliseconds=1)


def parse_date(value: str, field: str = "date") -> Date:
    """Strict YYYY-MM-DD (a real calendar date) or 422."""
    if not re.match(DATE_RE, value or ""):
        raise unprocessable("must be YYYY-MM-DD", field)
    try:
        return Date.fromisoformat(value)
    except ValueError:
        raise unprocessable("not a valid calendar date", field)


def month_bounds(month: str) -> tuple[Date, Date]:
    if not re.match(MONTH_RE, month or ""):
        raise unprocessable("must be YYYY-MM", "month")
    year, mon = int(month[:4]), int(month[5:])
    if year < 1:
        raise unprocessable("invalid year", "month")
    first = Date(year, mon, 1)
    nxt = Date(year + (mon == 12), mon % 12 + 1, 1) if year < 9999 else Date(year, 12, 31) + timedelta(days=1)
    return first, nxt - timedelta(days=1)


def half_up(value: Any, places: int) -> Optional[float]:
    """Round half-up (R8). round(x, 9) first removes binary-float noise so 0.12345 really is a tie."""
    if value is None:
        return None
    dec = Decimal(repr(round(float(value), 9)))
    return float(dec.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def _hm(value: str) -> tuple[int, int]:
    hh, mm = value.split(":")
    return int(hh), int(mm)


def is_overnight(shift_start: str, shift_end: str) -> bool:
    return shift_end <= shift_start  # zero-padded HH:MM compares correctly as text


def attendance_date(punch_in: datetime, shift_start: str, shift_end: str) -> str:
    """R1: IST calendar date of the punch-in; an overnight shift's early-morning punch-in belongs to the day before."""
    local = punch_in.astimezone(IST)
    day = local.date()
    if is_overnight(shift_start, shift_end) and local.time() < TimeOfDay(*_hm(shift_end)):
        day -= timedelta(days=1)
    return day.isoformat()


def _at(day: str, hhmm: str) -> datetime:
    return datetime.combine(Date.fromisoformat(day), TimeOfDay(*_hm(hhmm)), tzinfo=IST)


def compute_late_minutes(punch_in: datetime, att_date: str, shift_start: str) -> int:
    """R2: late only when strictly more than 10:00 after shift start; then whole minutes since shift start."""
    seconds = int((punch_in - _at(att_date, shift_start)).total_seconds())
    return seconds // 60 if seconds > GRACE_SECONDS else 0


def compute_work_hours(punch_in: datetime, punch_out: datetime) -> float:
    """R4: seconds / 3600, 2 decimals, half-up (Decimal, not float round())."""
    seconds = int((punch_out - punch_in).total_seconds())
    return float((Decimal(seconds) / Decimal(3600)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def compute_overtime(punch_out: datetime, att_date: str, shift_start: str, shift_end: str) -> int:
    """R3: whole minutes after shift end, counted only when >= 30. Overnight shifts end on the next day."""
    end = _at(att_date, shift_end)
    if is_overnight(shift_start, shift_end):
        end += timedelta(days=1)
    minutes = int((punch_out - end).total_seconds()) // 60
    return minutes if minutes >= MIN_OVERTIME_MINUTES else 0


def derive(emp: dict, att_date: str, punch_in: datetime, punch_out: Optional[datetime]) -> dict:
    """All stored derived fields for a presence record (see the table in DATA_MODEL.md)."""
    out = {
        "late_minutes": compute_late_minutes(punch_in, att_date, emp["shift_start"]),
        "work_hours": None,
        "overtime_minutes": 0,
        "half_day": False,
    }
    if punch_out is not None:
        hours = compute_work_hours(punch_in, punch_out)
        out["work_hours"] = hours
        out["overtime_minutes"] = compute_overtime(punch_out, att_date, emp["shift_start"], emp["shift_end"])
        out["half_day"] = Decimal(repr(hours)) < HALF_DAY_HOURS  # R5 on the rounded value
    return out


def working_days(joined_on: str, first: Date, last: Date) -> int:
    """R7: Mon-Fri between max(joined_on, first of month) and the last day of the month."""
    start = max(first, Date.fromisoformat(joined_on))
    return sum(1 for i in range((last - start).days + 1) if (start + timedelta(days=i)).weekday() < 5)


# =========================================================================== #
# 3. Models and serialisers
# =========================================================================== #
EpochMs = Annotated[int, Field(strict=True, ge=MS_MIN, le=MS_MAX)]  # rejects floats, strings, bools, seconds


class EmployeeIn(BaseModel):
    emp_code: str = Field(pattern=r"^EMP[0-9]{4,6}$")
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    department: str = Field(min_length=1, max_length=50)
    shift_start: str = Field("09:30", pattern=HHMM_RE)
    shift_end: str = Field("18:30", pattern=HHMM_RE)
    joined_on: str = Field(pattern=DATE_RE)

    @model_validator(mode="after")
    def _check(self):
        Date.fromisoformat(self.joined_on)  # ValueError -> 422
        if self.shift_start == self.shift_end:
            raise ValueError("shift_start must differ from shift_end")
        return self


class PunchInIn(BaseModel):
    emp_code: str = Field(min_length=1)
    punched_at: Optional[EpochMs] = None
    status: Literal["PRESENT", "WFH", "ON_DUTY"] = "PRESENT"


class PunchOutIn(BaseModel):
    emp_code: str = Field(min_length=1)
    punched_at: Optional[EpochMs] = None


class RegularizeIn(BaseModel):
    status: Optional[StatusT] = None
    punch_in: Optional[EpochMs] = None
    punch_out: Optional[EpochMs] = None
    reason: str = Field(min_length=5, max_length=200)
    regularized_by: str = Field(min_length=1, max_length=50)

    @model_validator(mode="before")
    @classmethod
    def _no_explicit_nulls(cls, data):
        if isinstance(data, dict):
            for key in ("status", "punch_in", "punch_out"):
                if key in data and data[key] is None:
                    raise ValueError(f"{key} must not be null; omit it to leave it unchanged")
        return data


def employee_out(doc: dict) -> dict:
    return {
        "emp_code": doc["emp_code"],
        "name": doc.get("name"),
        "email": doc.get("email"),
        "department": doc.get("department"),
        "shift_start": doc.get("shift_start"),
        "shift_end": doc.get("shift_end"),
        "joined_on": doc.get("joined_on"),
        "created_at": dt_to_ms(doc.get("created_at")),
    }


def record_out(doc: dict) -> dict:
    """Stored attendance document -> API shape: no _id, epoch-ms instants, legacy gaps filled in."""
    history = []
    for entry in doc.get("history") or []:
        changes = {}
        for key, change in (entry.get("changes") or {}).items():
            if key in ("punch_in", "punch_out"):
                change = {"from": dt_to_ms(change.get("from")), "to": dt_to_ms(change.get("to"))}
            changes[key] = change
        history.append(
            {"at": dt_to_ms(entry.get("at")), "by": entry.get("by"), "reason": entry.get("reason"), "changes": changes}
        )
    return {
        "emp_code": doc["emp_code"],
        "date": doc["date"],
        "status": doc["status"],
        "punch_in": dt_to_ms(doc.get("punch_in")),
        "punch_out": dt_to_ms(doc.get("punch_out")),
        "work_hours": doc.get("work_hours"),
        "late_minutes": doc.get("late_minutes") or 0,
        "overtime_minutes": doc.get("overtime_minutes") or 0,
        "half_day": bool(doc.get("half_day", False)),
        "history": history,
    }


def get_employee(emp_code: str) -> dict:
    emp = db[EMPLOYEES].find_one({"emp_code": emp_code}, {"_id": 0})
    if emp is None:
        raise HTTPException(404, "employee not found")
    return emp


# =========================================================================== #
# 4. Employees and attendance
# =========================================================================== #
@app.get("/health")
def health():
    try:
        client.admin.command("ping")
    except PyMongoError:
        raise HTTPException(503, "database unavailable")
    ensure_indexes()
    return {"status": "ok"}


@app.post("/employees", status_code=201)
def create_employee(body: EmployeeIn):
    doc = body.model_dump()
    doc["created_at"] = now_utc()
    try:
        db[EMPLOYEES].insert_one(doc)  # the unique index decides the race, not a prior find_one
    except DuplicateKeyError:
        raise HTTPException(409, "emp_code already exists")
    return employee_out(doc)


@app.get("/employees")
def list_employees(
    department: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    flt = {"department": department} if department is not None else {}
    total = db[EMPLOYEES].count_documents(flt)
    cursor = db[EMPLOYEES].find(flt).sort("emp_code", ASCENDING).skip((page - 1) * page_size).limit(page_size)
    return {"items": [employee_out(d) for d in cursor], "total": total, "page": page, "page_size": page_size}


@app.post("/attendance/punch-in", status_code=201)
def punch_in(body: PunchInIn):
    emp = get_employee(body.emp_code)
    ts = ms_to_dt(body.punched_at) if body.punched_at is not None else now_utc()
    day = attendance_date(ts, emp["shift_start"], emp["shift_end"])
    doc = {
        "emp_code": body.emp_code,
        "date": day,
        "status": body.status,
        "punch_in": ts,
        "punch_out": None,
        **derive(emp, day, ts, None),
        "history": [],
    }
    try:
        db[LOGS].insert_one(doc)  # unique (emp_code, date): exactly one of N concurrent requests succeeds
    except DuplicateKeyError:
        raise HTTPException(409, "already punched in for this date")
    return record_out(doc)


@app.post("/attendance/punch-out")
def punch_out(body: PunchOutIn):
    emp = get_employee(body.emp_code)
    ts = ms_to_dt(body.punched_at) if body.punched_at is not None else now_utc()
    rec = db[LOGS].find_one(
        {"emp_code": body.emp_code, "punch_in": {"$lte": ts}}, sort=[("punch_in", DESCENDING)]
    )
    if rec is None:
        raise HTTPException(404, "no punch-in found")
    if rec.get("punch_out") is not None:
        raise HTTPException(409, "already punched out")
    p_in = aware(rec["punch_in"])
    if ts <= p_in:
        raise unprocessable("punched_at must be after the punch-in", "punched_at")
    if ts - p_in > timedelta(hours=24):
        raise unprocessable("punch-out is more than 24 hours after the punch-in", "punched_at")
    d = derive(emp, rec["date"], p_in, ts)
    updated = db[LOGS].find_one_and_update(
        # the punch_out: None guard makes the update atomic - only one concurrent punch-out can match
        {"_id": rec["_id"], "punch_out": None},
        {"$set": {"punch_out": ts, "work_hours": d["work_hours"],
                  "overtime_minutes": d["overtime_minutes"], "half_day": d["half_day"]}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise HTTPException(409, "already punched out")
    return record_out(updated)


def attendance_query(emp_code, date_from, date_to, status):
    """Filter, sort and index hint for GET /attendance. Shared with the explain endpoint."""
    d_from = parse_date(date_from, "date_from") if date_from else None
    d_to = parse_date(date_to, "date_to") if date_to else None
    if d_from and d_to and d_from > d_to:
        raise unprocessable("date_from must not be after date_to", "date_from")
    flt: dict[str, Any] = {}
    if emp_code:
        flt["emp_code"] = emp_code
    if d_from or d_to:
        flt["date"] = {}
        if d_from:
            flt["date"]["$gte"] = d_from.isoformat()
        if d_to:
            flt["date"]["$lte"] = d_to.isoformat()
    if status:
        flt["status"] = status
    sort = [("date", DESCENDING), ("emp_code", ASCENDING)]
    hint = "uq_emp_date" if emp_code else "ix_status_date_emp" if status else "ix_date_emp"
    return flt, sort, hint


@app.get("/attendance")
def list_attendance(
    emp_code: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[StatusT] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    flt, sort, hint = attendance_query(emp_code, date_from, date_to, status)
    total = db[LOGS].count_documents(flt)
    cursor = db[LOGS].find(flt).sort(sort).hint(hint).skip((page - 1) * page_size).limit(page_size)
    return {"items": [record_out(d) for d in cursor], "total": total, "page": page, "page_size": page_size}


def plan_regularization(emp: dict, rec: dict, body: RegularizeIn) -> tuple[dict, dict]:
    """Return (new field values, changes) for a correction, or raise 422. Pure: touches no database."""
    new_status = body.status or rec["status"]
    if new_status in NON_PRESENT_STATUSES:
        if body.punch_in is not None or body.punch_out is not None:
            raise unprocessable(f"status {new_status} clears the punch times; do not send punch_in/punch_out")
        p_in = p_out = None
        derived = {"work_hours": None, "late_minutes": 0, "overtime_minutes": 0, "half_day": False}
    else:
        p_in = ms_to_dt(body.punch_in) if body.punch_in is not None else aware(rec.get("punch_in"))
        p_out = ms_to_dt(body.punch_out) if body.punch_out is not None else aware(rec.get("punch_out"))
        if p_in is None:
            raise unprocessable(f"status {new_status} requires a punch_in", "punch_in")
        if attendance_date(p_in, emp["shift_start"], emp["shift_end"]) != rec["date"]:
            raise unprocessable("punch_in must stay on the record's attendance date", "punch_in")
        if p_out is not None and (p_out <= p_in or p_out - p_in > timedelta(hours=24)):
            raise unprocessable("punch_out must be after punch_in and within 24 hours", "punch_out")
        derived = derive(emp, rec["date"], p_in, p_out)

    new = {"status": new_status, "punch_in": p_in, "punch_out": p_out, **derived}
    old = {
        "status": rec["status"],
        "punch_in": aware(rec.get("punch_in")),
        "punch_out": aware(rec.get("punch_out")),
        "work_hours": rec.get("work_hours"),
        "late_minutes": rec.get("late_minutes") or 0,
        "overtime_minutes": rec.get("overtime_minutes") or 0,
        "half_day": bool(rec.get("half_day", False)),
    }
    if all(new[k] == old[k] for k in ("status", "punch_in", "punch_out")):
        raise unprocessable("the request changes nothing")
    changes = {k: {"from": old[k], "to": new[k]} for k in new if new[k] != old[k]}
    return new, changes


@app.patch("/attendance/{emp_code}/{date}")
def regularize(emp_code: str, body: RegularizeIn, date: str = Path(pattern=DATE_RE)):
    parse_date(date, "date")
    emp = get_employee(emp_code)
    for _attempt in range(5):
        rec = db[LOGS].find_one({"emp_code": emp_code, "date": date})
        if rec is None:
            raise HTTPException(404, "no attendance record for that date")
        new, changes = plan_regularization(emp, rec, body)
        entry = {"at": now_utc(), "by": body.regularized_by, "reason": body.reason, "changes": changes}
        n = len(rec.get("history") or [])
        # Optimistic concurrency: apply only if the record is exactly as we read it (same history length,
        # same status and punch times). Otherwise somebody else changed it: re-read and plan again.
        guard = {
            "_id": rec["_id"],
            "status": rec["status"],
            "punch_in": rec.get("punch_in"),
            "punch_out": rec.get("punch_out"),
            "history": {"$size": n} if "history" in rec else {"$exists": False},
        }
        updated = db[LOGS].find_one_and_update(
            guard, {"$set": new, "$push": {"history": entry}}, return_document=ReturnDocument.AFTER
        )
        if updated is not None:
            return record_out(updated)
    raise HTTPException(409, "record is being modified concurrently; retry")


# =========================================================================== #
# 5. Analytics (all aggregation pipelines run inside MongoDB)
# =========================================================================== #
_DOW = {"$dayOfWeek": {"$dateFromString": {"dateString": "$date", "format": "%Y-%m-%d"}}}  # 1=Sun .. 7=Sat
_IS_WEEKDAY = {"$in": [_DOW, [2, 3, 4, 5, 6]]}
_IS_PRESENT = {"$in": ["$status", PRESENT_STATUSES]}
_WEIGHT = {"$cond": [{"$eq": [{"$ifNull": ["$half_day", False]}, True]}, 0.5, 1]}  # R5: half day = 0.5
_LATE = {"$ifNull": ["$late_minutes", 0]}
_HAS_HOURS = {"$and": [_IS_PRESENT, {"$isNumber": "$work_hours"}]}


def _count_if(cond: dict) -> dict:
    return {"$sum": {"$cond": [cond, 1, 0]}}


def stats_group(group_id: Any) -> dict:
    """$group accumulating every figure the monthly / department endpoints need, from STORED derived values."""
    return {
        "$group": {
            "_id": group_id,
            "present_days": {"$sum": {"$cond": [{"$and": [_IS_PRESENT, _IS_WEEKDAY]}, _WEIGHT, 0]}},  # R6 + R7
            "work_sum": {"$sum": {"$cond": [_HAS_HOURS, "$work_hours", 0]}},
            "work_cnt": _count_if(_HAS_HOURS),
            "late_count": _count_if({"$gt": [_LATE, 0]}),
            "late_sum": {"$sum": _LATE},
            "ot_sum": {"$sum": {"$ifNull": ["$overtime_minutes", 0]}},
            "leave_count": _count_if({"$eq": ["$status", "LEAVE"]}),
            "on_duty_count": _count_if({"$eq": ["$status", "ON_DUTY"]}),
        }
    }


def build_employee_monthly(emp_code: str, month: str):
    first, last = month_bounds(month)
    pipeline = [
        {"$match": {"emp_code": emp_code, "date": {"$gte": first.isoformat(), "$lte": last.isoformat()}}},
        stats_group(None),
    ]
    return LOGS, pipeline, "uq_emp_date"


@app.get("/analytics/employees/{emp_code}/monthly")
def employee_monthly(emp_code: str, month: str = Query(pattern=MONTH_RE)):
    first, last = month_bounds(month)
    emp = get_employee(emp_code)
    coll, pipeline, hint = build_employee_monthly(emp_code, month)
    s = next(iter(db[coll].aggregate(pipeline, hint=hint)), {})
    wd = working_days(emp["joined_on"], first, last)
    present = s.get("present_days", 0)
    return {
        "emp_code": emp_code,
        "month": month,
        "working_days": wd,
        "present_days": float(present),
        "leave_days": s.get("leave_count", 0),
        "late_count": s.get("late_count", 0),
        "total_late_minutes": s.get("late_sum", 0),
        "total_overtime_minutes": s.get("ot_sum", 0),
        "attendance_pct": half_up(Decimal(repr(present)) / wd * 100, 2) if wd else None,
    }


def build_department_summary(month: str, department: Optional[str]):
    first, last = month_bounds(month)
    f, t = first.isoformat(), last.isoformat()
    match: dict[str, Any] = {"joined_on": {"$lte": t}}  # R9
    if department is not None:
        match["department"] = department
    pipeline = [
        {"$match": match},
        # one correlated sub-pipeline per employee: employees without logs simply get an empty array
        {"$lookup": {
            "from": LOGS,
            "let": {"c": "$emp_code"},
            "pipeline": [
                {"$match": {"$expr": {"$and": [
                    {"$eq": ["$emp_code", "$$c"]}, {"$gte": ["$date", f]}, {"$lte": ["$date", t]}]}}},
                stats_group(None),
            ],
            "as": "s",
        }},
        {"$group": {
            "_id": "$department",
            "headcount": {"$sum": 1},  # every joined employee counts once, logs or not
            "present_days": {"$sum": {"$sum": "$s.present_days"}},
            "work_sum": {"$sum": {"$sum": "$s.work_sum"}},
            "work_cnt": {"$sum": {"$sum": "$s.work_cnt"}},
            "late_count": {"$sum": {"$sum": "$s.late_count"}},
            "late_sum": {"$sum": {"$sum": "$s.late_sum"}},
            "leave_count": {"$sum": {"$sum": "$s.leave_count"}},
            "on_duty_count": {"$sum": {"$sum": "$s.on_duty_count"}},
        }},
        {"$sort": {"_id": 1}},
    ]
    hint = "ix_dept_joined" if department is not None else "ix_joined"
    return EMPLOYEES, pipeline, hint


@app.get("/analytics/departments/summary")
def department_summary(month: str = Query(pattern=MONTH_RE), department: Optional[str] = None):
    coll, pipeline, hint = build_department_summary(month, department)
    items = []
    for r in db[coll].aggregate(pipeline, hint=hint):
        items.append({
            "department": r["_id"],
            "headcount": r["headcount"],
            "present_days": float(r["present_days"]),
            # mean over records (sum of hours / number of records), not a mean of per-employee means
            "avg_work_hours": half_up(r["work_sum"] / r["work_cnt"], 2) if r["work_cnt"] else None,
            "late_count": r["late_count"],
            "total_late_minutes": r["late_sum"],
            "leave_count": r["leave_count"],
            "on_duty_count": r["on_duty_count"],
        })
    return {"month": month, "items": items}


def build_late_leaderboard(month: str, limit: int, department: Optional[str]):
    first, last = month_bounds(month)
    pipeline: list[dict] = [
        {"$match": {"date": {"$gte": first.isoformat(), "$lte": last.isoformat()}}},
        {"$group": {"_id": "$emp_code", "total": {"$sum": _LATE}, "late_count": _count_if({"$gt": [_LATE, 0]})}},
        {"$match": {"total": {"$gt": 0}}},
        {"$lookup": {"from": EMPLOYEES, "localField": "_id", "foreignField": "emp_code", "as": "e"}},
        {"$unwind": "$e"},  # logs of unknown employees disappear here
    ]
    if department is not None:
        pipeline.append({"$match": {"e.department": department}})  # rank inside the department only
    pipeline += [
        # $rank = standard competition ranking (1, 2, 2, 4): ties share a rank, the next rank is skipped
        {"$setWindowFields": {"sortBy": {"total": -1}, "output": {"rank": {"$rank": {}}}}},
        {"$match": {"rank": {"$lte": limit}}},  # limit applies AFTER ranking
        {"$sort": {"total": -1, "_id": 1}},
        {"$project": {"_id": 0, "rank": 1, "emp_code": "$_id", "name": "$e.name", "department": "$e.department",
                      "total_late_minutes": "$total", "late_count": 1}},
    ]
    return LOGS, pipeline, "ix_date_emp"


@app.get("/analytics/leaderboard/late")
def late_leaderboard(
    month: str = Query(pattern=MONTH_RE), limit: int = Query(10, ge=1, le=50), department: Optional[str] = None
):
    coll, pipeline, hint = build_late_leaderboard(month, limit, department)
    return {"month": month, "items": list(db[coll].aggregate(pipeline, hint=hint))}


MAX_TREND_DAYS = 92


def check_trend_range(frm: str, to: str) -> tuple[Date, Date]:
    d_from, d_to = parse_date(frm, "from"), parse_date(to, "to")
    if d_to < d_from:
        raise unprocessable("'to' must not be before 'from'", "to")
    if (d_to - d_from).days + 1 > MAX_TREND_DAYS:
        raise unprocessable(f"range exceeds {MAX_TREND_DAYS} days", "to")
    return d_from, d_to


def build_department_trend(department: str, d_from: Date, d_to: Date):
    f, t = d_from.isoformat(), d_to.isoformat()
    lower = datetime(d_from.year, d_from.month, d_from.day, tzinfo=UTC)
    upper = datetime(d_to.year, d_to.month, d_to.day, tzinfo=UTC) + timedelta(days=1)  # bound is exclusive
    pipeline = [
        {"$match": {"department": department}},
        {"$lookup": {
            "from": LOGS,
            "let": {"c": "$emp_code"},
            "pipeline": [
                {"$match": {"$expr": {"$and": [
                    {"$eq": ["$emp_code", "$$c"]}, {"$gte": ["$date", f]}, {"$lte": ["$date", t]}]}}},
                {"$project": {"_id": 0, "date": 1, "status": 1, "half_day": 1, "late_minutes": 1}},
            ],
            "as": "logs",
        }},
        {"$unwind": "$logs"},
        {"$group": {
            "_id": "$logs.date",
            "present_count": {"$sum": {"$cond": [{"$in": ["$logs.status", PRESENT_STATUSES]},
                                                 {"$cond": [{"$eq": [{"$ifNull": ["$logs.half_day", False]}, True]}, 0.5, 1]},
                                                 0]}},
            "late_count": {"$sum": {"$cond": [{"$gt": [{"$ifNull": ["$logs.late_minutes", 0]}, 0]}, 1, 0]}},
        }},
        # a zero-valued seed row for the first day guarantees $densify has input even if nobody has any log
        {"$unionWith": {"pipeline": [{"$documents": [{"_id": f, "present_count": 0, "late_count": 0}]}]}},
        {"$group": {"_id": "$_id", "present_count": {"$sum": "$present_count"}, "late_count": {"$sum": "$late_count"}}},
        {"$addFields": {"d": {"$dateFromString": {"dateString": "$_id", "format": "%Y-%m-%d"}}}},
        # gap filling: one row per calendar day, weekends and empty days included
        {"$densify": {"field": "d", "range": {"step": 1, "unit": "day", "bounds": [lower, upper]}}},
        {"$addFields": {
            "date": {"$dateToString": {"date": "$d", "format": "%Y-%m-%d"}},
            "present_count": {"$ifNull": ["$present_count", 0]},
            "late_count": {"$ifNull": ["$late_count", 0]},
        }},
        # R9 headcount per day: department employees who joined on or before that day
        {"$lookup": {
            "from": EMPLOYEES,
            "let": {"day": "$date"},
            "pipeline": [{"$match": {"department": department, "$expr": {"$lte": ["$joined_on", "$$day"]}}},
                         {"$count": "n"}],
            "as": "hc",
        }},
        {"$addFields": {
            "headcount": {"$ifNull": [{"$first": "$hc.n"}, 0]},
            "is_working_day": {"$in": [{"$dayOfWeek": "$d"}, [2, 3, 4, 5, 6]]},
        }},
        {"$addFields": {"rate": {"$cond": [
            {"$and": ["$is_working_day", {"$gt": ["$headcount", 0]}]},
            {"$divide": ["$present_count", "$headcount"]},
            None,
        ]}}},
        # current row + up to 6 preceding rows of the requested range; $avg ignores null rates
        {"$setWindowFields": {"sortBy": {"d": 1}, "output": {"ma": {"$avg": "$rate", "window": {"documents": [-6, 0]}}}}},
        {"$sort": {"d": 1}},
        {"$project": {"_id": 0, "date": 1, "is_working_day": 1, "headcount": 1, "present_count": 1,
                      "late_count": 1, "rate": 1, "ma": 1}},
    ]
    return EMPLOYEES, pipeline, "ix_dept_joined"


@app.get("/analytics/departments/{department}/trend")
def department_trend(department: str, frm: str = Query(alias="from"), to: str = Query()):
    d_from, d_to = check_trend_range(frm, to)
    if db[EMPLOYEES].count_documents({"department": department}, limit=1) == 0:
        raise HTTPException(404, "unknown department")
    coll, pipeline, hint = build_department_trend(department, d_from, d_to)
    items = [{
        "date": r["date"],
        "is_working_day": r["is_working_day"],
        "headcount": r["headcount"],
        "present_count": float(r["present_count"]),
        "late_count": r["late_count"],
        "attendance_rate": half_up(r["rate"], 4),
        "moving_avg_7d": half_up(r.get("ma"), 4),
    } for r in db[coll].aggregate(pipeline, hint=hint)]
    return {"department": department, "items": items}


# =========================================================================== #
# 6. Admin: explain
# =========================================================================== #
def _require(**params):
    missing = [k for k, v in params.items() if v is None]
    if missing:
        raise HTTPException(422, [{"type": "missing", "loc": ["query", k], "msg": "Field required"} for k in missing])


@app.get("/admin/explain/{endpoint}")
def explain(
    endpoint: Literal["attendance_list", "employee_monthly", "department_summary", "late_leaderboard", "department_trend"],
    emp_code: Optional[str] = None,
    month: Optional[str] = Query(None, pattern=MONTH_RE),
    department: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[StatusT] = None,
    frm: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Raw explain('executionStats') of the endpoint's main query, built by the very same functions."""
    if endpoint == "attendance_list":
        flt, sort, hint = attendance_query(emp_code, date_from, date_to, status)
        coll = LOGS
        command = {"find": LOGS, "filter": flt, "sort": dict(sort), "hint": hint,
                   "skip": (page - 1) * page_size, "limit": page_size}
    else:
        if endpoint == "employee_monthly":
            _require(emp_code=emp_code, month=month)
            coll, pipeline, hint = build_employee_monthly(emp_code, month)
        elif endpoint == "department_summary":
            _require(month=month)
            coll, pipeline, hint = build_department_summary(month, department)
        elif endpoint == "late_leaderboard":
            _require(month=month)
            coll, pipeline, hint = build_late_leaderboard(month, limit, department)
        else:
            _require(department=department, **{"from": frm, "to": to})
            coll, pipeline, hint = build_department_trend(department, *check_trend_range(frm, to))
        command = {"aggregate": coll, "pipeline": pipeline, "cursor": {}, "hint": hint}
    result = db.command({"explain": command, "verbosity": "executionStats"})
    return {"endpoint": endpoint, "collection": coll, "explain": json.loads(json_util.dumps(result))}


# =========================================================================== #
# 7. Dashboard UI  →  see app/ui.py  (UI_HTML imported at top of file)
# =========================================================================== #
UI_HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Attendance Console</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2430;--mute:#667085;--line:#e4e7ec;--acc:#2f5bea;--ok:#12805c;--bad:#c0392b;--r:10px}
@media(prefers-color-scheme:dark){:root{--bg:#0f141b;--card:#171e28;--ink:#e8edf4;--mute:#93a0b3;--line:#263041;--acc:#6f8fff;--ok:#3fbf94;--bad:#ff7a6b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:14px 20px;border-bottom:1px solid var(--line);background:var(--card);position:sticky;top:0;z-index:2}
h1{font-size:16px;margin:0}nav{display:flex;gap:4px;flex-wrap:wrap}
nav button{border:0;background:none;color:var(--mute);padding:7px 12px;border-radius:8px;cursor:pointer;font:inherit}
nav button.on{background:var(--acc);color:#fff}
main{max-width:1100px;margin:0 auto;padding:18px 16px 60px}
section{display:none}section.on{display:block}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:16px;margin-bottom:16px}
.card h2{font-size:14px;margin:0 0 10px}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:end;margin-bottom:10px}
label{display:flex;flex-direction:column;gap:3px;font-size:12px;color:var(--mute)}
input,select{font:inherit;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:7px;padding:7px 9px;min-width:130px}
button.act{background:var(--acc);color:#fff;border:0;border-radius:7px;padding:8px 14px;cursor:pointer;font:inherit}
button.ghost{background:none;color:var(--acc);border:1px solid var(--line);border-radius:7px;padding:7px 12px;cursor:pointer;font:inherit}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
th{color:var(--mute);font-weight:600;font-size:12px}.scroll{overflow-x:auto}
.msg{margin:8px 0;padding:8px 10px;border-radius:7px;font-size:13px}.msg.ok{background:color-mix(in srgb,var(--ok) 15%,transparent);color:var(--ok)}
.msg.err{background:color-mix(in srgb,var(--bad) 15%,transparent);color:var(--bad)}
.pill{padding:2px 8px;border-radius:99px;font-size:11px;background:var(--bg);border:1px solid var(--line)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px}.stat{border:1px solid var(--line);border-radius:8px;padding:10px}
.stat b{display:block;font-size:20px}.stat span{color:var(--mute);font-size:12px}.empty{color:var(--mute);padding:8px 0}
svg text{fill:var(--mute);font-size:10px}
</style></head><body>
<header><h1>Attendance Console</h1><nav id="nav"></nav><a style="margin-left:auto;color:var(--acc)" href="/docs">API docs</a></header>
<main>
<section id="analytics">
 <div class="card"><div class="row"><label>Month<input id="a_month" type="month"></label><label>Department<input id="a_dept" placeholder="all"></label>
 <button class="act" onclick="loadAnalytics()">Load</button></div><div id="a_msg"></div></div>
 <div class="card"><h2>Department summary</h2><div class="scroll" id="a_sum"></div></div>
 <div class="card"><h2>Late leaderboard</h2><div class="row"><label>Top<input id="a_limit" type="number" min="1" max="50" value="10" style="min-width:70px"></label></div><div class="scroll" id="a_lb"></div></div>
 <div class="card"><h2>Employee month</h2><div class="row"><label>Employee code<input id="a_emp" placeholder="EMP0001"></label><button class="ghost" onclick="loadEmp()">Show</button></div><div id="a_emp_out"></div></div>
 <div class="card"><h2>Department trend</h2><div class="row"><label>Department<input id="t_dept" placeholder="Engineering"></label><label>From<input id="t_from" type="date"></label><label>To<input id="t_to" type="date"></label><button class="ghost" onclick="loadTrend()">Plot</button></div><div id="t_out"></div></div>
</section>
<section id="attendance">
 <div class="card"><h2>Punch</h2><div class="row"><label>Employee code<input id="p_emp" placeholder="EMP0001"></label>
 <label>Status<select id="p_status"><option>PRESENT</option><option>WFH</option><option>ON_DUTY</option></select></label>
 <label>Time (blank = now)<input id="p_time" type="datetime-local" step="1"></label>
 <button class="act" onclick="punch('in')">Punch in</button><button class="ghost" onclick="punch('out')">Punch out</button></div><div id="p_msg"></div></div>
 <div class="card"><h2>Records</h2><div class="row"><label>Employee<input id="l_emp"></label><label>From<input id="l_from" type="date"></label><label>To<input id="l_to" type="date"></label>
 <label>Status<select id="l_status"><option value="">any</option><option>PRESENT</option><option>WFH</option><option>ON_DUTY</option><option>ABSENT</option><option>LEAVE</option></select></label>
 <button class="act" onclick="loadLogs(1)">Search</button></div><div id="l_msg"></div><div class="scroll" id="l_out"></div><div class="row" id="l_pg" style="margin-top:10px"></div></div>
 <div class="card"><h2>Correct a record</h2><div class="row"><label>Employee<input id="r_emp"></label><label>Date<input id="r_date" type="date"></label>
 <label>Status<select id="r_status"><option value="">unchanged</option><option>PRESENT</option><option>WFH</option><option>ON_DUTY</option><option>ABSENT</option><option>LEAVE</option></select></label>
 <label>Punch in<input id="r_in" type="datetime-local" step="1"></label><label>Punch out<input id="r_out" type="datetime-local" step="1"></label></div>
 <div class="row"><label>Reason<input id="r_reason" style="min-width:260px" placeholder="min 5 characters"></label><label>By<input id="r_by" value="hr.admin"></label><button class="act" onclick="regularize()">Apply correction</button></div><div id="r_msg"></div></div>
</section>
<section id="employees">
 <div class="card"><h2>New employee</h2><div class="row"><label>Code<input id="e_code" placeholder="EMP0042"></label><label>Name<input id="e_name"></label><label>Email<input id="e_email"></label>
 <label>Department<input id="e_dept"></label><label>Shift start<input id="e_ss" value="09:30" style="min-width:80px"></label><label>Shift end<input id="e_se" value="18:30" style="min-width:80px"></label>
 <label>Joined on<input id="e_join" type="date"></label><button class="act" onclick="addEmp()">Create</button></div><div id="e_msg"></div></div>
 <div class="card"><h2>Employees</h2><div class="row"><label>Department<input id="f_dept" placeholder="all"></label><button class="act" onclick="loadEmps(1)">Filter</button></div><div class="scroll" id="f_out"></div><div class="row" id="f_pg" style="margin-top:10px"></div></div>
</section>
</main>
<script>
const $=id=>document.getElementById(id);
const IST=330*60000; // the UI works in IST, like the business rules
const fmt=ms=>ms==null?'-':new Date(ms+IST).toISOString().slice(0,19).replace('T',' ');
const toMs=v=>v?Date.parse(v+(v.length===16?':00':'')+'+05:30'):undefined;
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function api(path,opt){const r=await fetch(path,opt);let b=null;try{b=await r.json()}catch(e){}
 if(!r.ok){const d=b&&b.detail;throw new Error(Array.isArray(d)?d.map(x=>(x.loc||[]).slice(1).join('.')+' '+x.msg).join('; '):(d||r.statusText))}return b}
const send=(m,body)=>({method:m,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
const say=(id,t,ok)=>{$(id).innerHTML=t?'<div class="msg '+(ok?'ok':'err')+'">'+esc(t)+'</div>':''};
function table(cols,rows){if(!rows.length)return '<div class="empty">No rows.</div>';
 return '<table><tr>'+cols.map(c=>'<th>'+esc(c[0])+'</th>').join('')+'</tr>'+rows.map(r=>'<tr>'+cols.map(c=>'<td>'+esc(c[1](r))+'</td>').join('')+'</tr>').join('')+'</table>'}
function pager(id,page,size,total,fn){const last=Math.max(1,Math.ceil(total/size));
 $(id).innerHTML='<button class="ghost" '+(page<=1?'disabled':'')+' onclick="'+fn+'('+(page-1)+')">Prev</button><span>Page '+page+' / '+last+' ('+total+' rows)</span><button class="ghost" '+(page>=last?'disabled':'')+' onclick="'+fn+'('+(page+1)+')">Next</button>'}
const qs=o=>Object.entries(o).filter(([k,v])=>v!==''&&v!=null).map(([k,v])=>k+'='+encodeURIComponent(v)).join('&');
async function loadAnalytics(){try{say('a_msg','');const m=$('a_month').value,d=$('a_dept').value;
 const s=await api('/analytics/departments/summary?'+qs({month:m,department:d}));
 $('a_sum').innerHTML=table([['Department',r=>r.department],['Headcount',r=>r.headcount],['Present days',r=>r.present_days],['Avg hours',r=>r.avg_work_hours??'-'],['Late',r=>r.late_count],['Late min',r=>r.total_late_minutes],['Leave',r=>r.leave_count],['On duty',r=>r.on_duty_count]],s.items);
 const l=await api('/analytics/leaderboard/late?'+qs({month:m,department:d,limit:$('a_limit').value}));
 $('a_lb').innerHTML=table([['Rank',r=>r.rank],['Code',r=>r.emp_code],['Name',r=>r.name],['Department',r=>r.department],['Late min',r=>r.total_late_minutes],['Late days',r=>r.late_count]],l.items)}catch(e){say('a_msg',e.message)}}
async function loadEmp(){try{const e=$('a_emp').value.trim(),m=$('a_month').value;const r=await api('/analytics/employees/'+encodeURIComponent(e)+'/monthly?month='+m);
 const st=[['Working days',r.working_days],['Present days',r.present_days],['Attendance %',r.attendance_pct??'n/a'],['Late count',r.late_count],['Late minutes',r.total_late_minutes],['Overtime min',r.total_overtime_minutes],['Leave days',r.leave_days]];
 $('a_emp_out').innerHTML='<div class="stats">'+st.map(x=>'<div class="stat"><b>'+esc(x[1])+'</b><span>'+x[0]+'</span></div>').join('')+'</div>'}catch(e){$('a_emp_out').innerHTML='<div class="msg err">'+esc(e.message)+'</div>'}}
async function loadTrend(){try{const d=$('t_dept').value.trim();const r=await api('/analytics/departments/'+encodeURIComponent(d)+'/trend?'+qs({from:$('t_from').value,to:$('t_to').value}));
 const W=1000,H=220,P=30,n=r.items.length,x=i=>P+i*(W-2*P)/Math.max(1,n-1),y=v=>H-P-v*(H-2*P);
 const path=(k)=>{let s='',pen=false;r.items.forEach((it,i)=>{const v=it[k];if(v==null){pen=false;return}s+=(pen?'L':'M')+x(i).toFixed(1)+' '+y(v).toFixed(1);pen=true});return s};
 const dots=r.items.map((it,i)=>it.attendance_rate==null?'<rect x="'+(x(i)-2)+'" y="'+(H-P-2)+'" width="4" height="4" fill="var(--line)"><title>'+it.date+' (non-working)</title></rect>':'<circle cx="'+x(i)+'" cy="'+y(it.attendance_rate)+'" r="3" fill="var(--acc)"><title>'+it.date+' '+it.attendance_rate+'</title></circle>').join('');
 $('t_out').innerHTML='<div class="scroll"><svg viewBox="0 0 '+W+' '+H+'" width="100%" style="min-width:640px">'+[0,.5,1].map(v=>'<line x1="'+P+'" x2="'+(W-P)+'" y1="'+y(v)+'" y2="'+y(v)+'" stroke="var(--line)"/><text x="2" y="'+(y(v)+3)+'">'+v+'</text>').join('')+
  '<path d="'+path('attendance_rate')+'" fill="none" stroke="var(--acc)" stroke-opacity=".35"/><path d="'+path('moving_avg_7d')+'" fill="none" stroke="var(--ok)" stroke-width="2.5"/>'+dots+
  '<text x="'+P+'" y="'+(H-8)+'">'+r.items[0].date+'</text><text x="'+(W-P-60)+'" y="'+(H-8)+'">'+r.items[n-1].date+'</text></svg></div><div class="empty"><span style="color:var(--acc)">●</span> daily rate &nbsp; <span style="color:var(--ok)">━</span> 7-day moving average &nbsp; (weekends have no rate)</div>'}
 catch(e){$('t_out').innerHTML='<div class="msg err">'+esc(e.message)+'</div>'}}
async function punch(kind){try{const b={emp_code:$('p_emp').value.trim()};const t=toMs($('p_time').value);if(t)b.punched_at=t;if(kind==='in')b.status=$('p_status').value;
 const r=await api('/attendance/punch-'+kind,send('POST',b));say('p_msg',kind==='in'?'Punched in for '+r.date+' (late '+r.late_minutes+' min)':'Punched out: '+r.work_hours+' h, overtime '+r.overtime_minutes+' min'+(r.half_day?', half day':''),true);loadLogs(1)}catch(e){say('p_msg',e.message)}}
async function loadLogs(p){try{const page=p||1,size=15;const r=await api('/attendance?'+qs({emp_code:$('l_emp').value.trim(),date_from:$('l_from').value,date_to:$('l_to').value,status:$('l_status').value,page,page_size:size}));say('l_msg','');
 $('l_out').innerHTML=table([['Date',r=>r.date],['Employee',r=>r.emp_code],['Status',r=>r.status],['In',r=>fmt(r.punch_in)],['Out',r=>fmt(r.punch_out)],['Hours',r=>r.work_hours??'-'],['Late',r=>r.late_minutes],['OT',r=>r.overtime_minutes],['Half',r=>r.half_day?'yes':''],['Edits',r=>r.history.length]],r.items);pager('l_pg',r.page,r.page_size,r.total,'loadLogs')}catch(e){say('l_msg',e.message)}}
async function regularize(){try{const b={reason:$('r_reason').value,regularized_by:$('r_by').value};if($('r_status').value)b.status=$('r_status').value;
 const a=toMs($('r_in').value),c=toMs($('r_out').value);if(a)b.punch_in=a;if(c)b.punch_out=c;
 const r=await api('/attendance/'+encodeURIComponent($('r_emp').value.trim())+'/'+$('r_date').value,send('PATCH',b));say('r_msg','Saved. History entries: '+r.history.length+' - '+Object.keys(r.history[r.history.length-1].changes).join(', '),true);loadLogs(1)}catch(e){say('r_msg',e.message)}}
async function addEmp(){try{const r=await api('/employees',send('POST',{emp_code:$('e_code').value.trim(),name:$('e_name').value,email:$('e_email').value,department:$('e_dept').value,shift_start:$('e_ss').value,shift_end:$('e_se').value,joined_on:$('e_join').value}));say('e_msg','Created '+r.emp_code,true);loadEmps(1)}catch(e){say('e_msg',e.message)}}
async function loadEmps(p){try{const page=p||1,size=15;const r=await api('/employees?'+qs({department:$('f_dept').value,page,page_size:size}));
 $('f_out').innerHTML=table([['Code',r=>r.emp_code],['Name',r=>r.name],['Department',r=>r.department],['Shift',r=>r.shift_start+' - '+r.shift_end],['Joined',r=>r.joined_on],['Email',r=>r.email]],r.items);pager('f_pg',r.page,r.page_size,r.total,'loadEmps')}catch(e){$('f_out').innerHTML='<div class="msg err">'+esc(e.message)+'</div>'}}
const tabs=[['analytics','Analytics'],['attendance','Attendance'],['employees','Employees']];
function show(id){tabs.forEach(t=>{$(t[0]).classList.toggle('on',t[0]===id);});[...$('nav').children].forEach((b,i)=>b.classList.toggle('on',tabs[i][0]===id));location.hash=id}
$('nav').innerHTML=tabs.map(t=>'<button onclick="show(\''+t[0]+'\')">'+t[1]+'</button>').join('');
const today=new Date(Date.now()+IST).toISOString().slice(0,10);$('a_month').value=today.slice(0,7);$('t_from').value=today.slice(0,8)+'01';$('t_to').value=today;
show(location.hash.slice(1)||'analytics');loadLogs(1);loadEmps(1);
</script></body></html>"""


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui():
    return HTMLResponse(UI_HTML)
