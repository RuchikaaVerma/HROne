"""Seed demo / load-test data that contains the awkward cases from the rules.

Usage:  python seed_demo.py            small hand-made set (ties, weekend, no-log employee, mid-month joiner, overnight, ...)
        python seed_demo.py --bulk     adds ~100,000 attendance records (to check indexes / explain plans)
Reads MONGO_URI / MONGO_DB like the app. It REPLACES both collections in that database - use a scratch DB."""
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
IST = timezone(timedelta(hours=5, minutes=30))
db = MongoClient(os.getenv("MONGO_URI") or "mongodb://localhost:27017", tz_aware=True)[os.getenv("MONGO_DB") or "attendance_db"]


def emp(code, name, dept, joined, start="09:30", end="18:30"):
    return {"emp_code": code, "name": name, "email": f"{code.lower()}@example.com", "department": dept,
            "shift_start": start, "shift_end": end, "joined_on": joined, "created_at": datetime.now(timezone.utc)}


def at(day, hh, mm, ss=0):
    return datetime(day.year, day.month, day.day, hh, mm, ss, tzinfo=IST).astimezone(timezone.utc)


def rec(code, day, status, p_in=None, p_out=None, wh=None, late=0, ot=0, half=False):
    return {"emp_code": code, "date": day.isoformat(), "status": status, "punch_in": p_in, "punch_out": p_out,
            "work_hours": wh, "late_minutes": late, "overtime_minutes": ot, "half_day": half, "history": []}


def small():
    e = [emp("EMP0001", "Asha Rao", "Engineering", "2026-01-05"), emp("EMP0002", "Ravi Iyer", "Engineering", "2026-01-05"),
         emp("EMP0003", "Meera Nair", "Engineering", "2026-01-05"), emp("EMP0004", "Kabir Shah", "Sales", "2026-01-05"),
         emp("EMP0005", "Night Owl", "Support", "2026-01-05", "22:00", "06:00"),
         emp("EMP0006", "No Logs", "Sales", "2026-01-05"), emp("EMP0007", "Mid Joiner", "Engineering", "2026-07-15"),
         emp("EMP0008", "Future Joiner", "Ops", "2026-09-01")]
    d = date(2026, 7, 6)
    logs = [rec("EMP0001", d, "PRESENT", at(d, 9, 28), at(d, 18, 35), 9.12),
            rec("EMP0002", d, "PRESENT", at(d, 10, 5), at(d, 19, 10), 9.08, 35, 40),   # tie on 35 late minutes ...
            rec("EMP0003", d, "PRESENT", at(d, 10, 5), at(d, 18, 40), 8.58, 35),       # ... with this one
            rec("EMP0004", d, "WFH", at(d, 9, 30), at(d, 13, 0), 3.5, 0, 0, True),
            rec("EMP0005", d, "PRESENT", at(d, 21, 55), at(d + timedelta(days=1), 6, 40), 8.75, 0, 40),
            rec("EMP0001", d + timedelta(days=1), "ON_DUTY", at(d + timedelta(days=1), 9, 30)),
            rec("EMP0003", d + timedelta(days=2), "LEAVE"), rec("EMP0004", d + timedelta(days=2), "ABSENT"),
            rec("EMP0002", date(2026, 7, 11), "PRESENT", at(date(2026, 7, 11), 10, 0), at(date(2026, 7, 11), 15, 0), 5.0, 30),  # Saturday
            rec("EMP0007", date(2026, 7, 15), "PRESENT", at(date(2026, 7, 15), 9, 30), at(date(2026, 7, 15), 18, 30), 9.0),
            rec("GHOST99", d, "PRESENT", at(d, 11, 0), at(d, 18, 0), 7.0, 90)]          # log of an unknown employee
    return e, logs


def bulk(n_emp=500, target=100_000):
    rnd = random.Random(42)
    depts = ["Engineering", "Sales", "Support", "Finance", "Ops", "HR", "Design", "Legal"]
    e = [emp(f"EMP{i:04d}", f"Employee {i}", depts[i % len(depts)], "2026-01-05") for i in range(1000, 1000 + n_emp)]
    logs, day = [], date(2026, 1, 5)
    while len(logs) < target:
        if day.weekday() < 5:
            for x in e:
                if rnd.random() < 0.9:
                    late = rnd.choice([0, 0, 0, 0, 12, 25, 40])
                    p_in = at(day, 9, 30) + timedelta(minutes=late if late else rnd.randint(-20, 9))
                    hrs = round(rnd.uniform(3, 10), 2)
                    logs.append(rec(x["emp_code"], day, rnd.choice(["PRESENT", "PRESENT", "WFH", "ON_DUTY"]), p_in,
                                    p_in + timedelta(seconds=int(hrs * 3600)), hrs, late, rnd.choice([0, 0, 35, 60]), hrs < 4.5))
        day += timedelta(days=1)
    return e, logs[:target]


if __name__ == "__main__":
    employees, logs = small()
    if "--bulk" in sys.argv:
        e2, l2 = bulk()
        employees, logs = employees + e2, logs + l2
    db.employees.delete_many({})
    db.attendance_logs.delete_many({})
    db.employees.insert_many(employees)
    db.attendance_logs.insert_many(logs)
    print(f"seeded {len(employees)} employees and {len(logs)} attendance records into '{db.name}'")
