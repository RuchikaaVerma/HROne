from datetime import datetime, timedelta, timezone

import pytest
from concurrent.futures import ThreadPoolExecutor

from .conftest import needs_mongo

IST = timezone(timedelta(hours=5, minutes=30))


def ms(y, mo, d, h, mi, s=0):
    return int(datetime(y, mo, d, h, mi, s, tzinfo=IST).timestamp() * 1000)


def emp(client, code="EMP0001", dept="Eng", start="09:30", end="18:30", joined="2026-01-05"):
    r = client.post("/employees", json={"emp_code": code, "name": "N " + code, "email": "a@b.co",
                                        "department": dept, "shift_start": start, "shift_end": end, "joined_on": joined})
    assert r.status_code == 201, r.text
    return r.json()


def test_employee_crud_and_validation(client, clean):
    e = emp(client)
    assert "_id" not in e and isinstance(e["created_at"], int)
    assert client.post("/employees", json={**e, "email": "a@b.co", "joined_on": "2026-01-05"}).status_code == 409
    bad = {"emp_code": "X1", "name": "n", "email": "nope", "department": "d", "joined_on": "2026-13-01"}
    assert client.post("/employees", json=bad).status_code == 422
    same = {"emp_code": "EMP0009", "name": "n", "email": "a@b.co", "department": "d", "shift_start": "09:00",
            "shift_end": "09:00", "joined_on": "2026-01-01"}
    assert client.post("/employees", json=same).status_code == 422


def test_employee_pagination(client, clean):
    for i in range(1, 6):
        emp(client, f"EMP000{i}", "A" if i % 2 else "B")
    r = client.get("/employees", params={"page": 1, "page_size": 2}).json()
    assert [x["emp_code"] for x in r["items"]] == ["EMP0001", "EMP0002"] and r["total"] == 5
    r = client.get("/employees", params={"department": "A", "page": 2, "page_size": 2}).json()
    assert [x["emp_code"] for x in r["items"]] == ["EMP0005"] and r["total"] == 3
    for q in ({"page": 0}, {"page_size": 101}, {"page_size": 0}):
        assert client.get("/employees", params=q).status_code == 422


def test_punch_in_out_flow(client, clean):
    emp(client)
    r = client.post("/attendance/punch-in", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 6, 10, 5, 30)})
    assert r.status_code == 201
    b = r.json()
    assert b["date"] == "2026-07-06" and b["late_minutes"] == 35 and b["punch_out"] is None and b["history"] == []
    assert "id" not in b and b["punch_in"] == ms(2026, 7, 6, 10, 5, 30)
    assert client.post("/attendance/punch-in", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 6, 11, 0)}).status_code == 409
    r = client.post("/attendance/punch-out", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 6, 19, 10)})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["work_hours"] == 9.08 and b["overtime_minutes"] == 40 and b["half_day"] is False
    assert client.post("/attendance/punch-out", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 6, 20, 0)}).status_code == 409


def test_punch_validation_and_404(client, clean):
    emp(client)
    assert client.post("/attendance/punch-in", json={"emp_code": "NOPE"}).status_code == 404
    for bad in (1783312500, 1783312500000.5, "1783312500000", True):
        assert client.post("/attendance/punch-in", json={"emp_code": "EMP0001", "punched_at": bad}).status_code == 422
    assert client.post("/attendance/punch-in", json={"emp_code": "EMP0001", "status": "ABSENT"}).status_code == 422
    assert client.post("/attendance/punch-out", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 6, 9, 0)}).status_code == 404
    client.post("/attendance/punch-in", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 6, 9, 0)})
    assert client.post("/attendance/punch-out", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 6, 9, 0)}).status_code == 422
    assert client.post("/attendance/punch-out", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 7, 9, 0, 1)}).status_code == 422


def test_overnight_punch_out_across_midnight(client, clean):
    emp(client, "EMP0005", start="22:00", end="06:00")
    r = client.post("/attendance/punch-in", json={"emp_code": "EMP0005", "punched_at": ms(2026, 7, 6, 21, 55)}).json()
    assert r["date"] == "2026-07-06"
    r = client.post("/attendance/punch-out", json={"emp_code": "EMP0005", "punched_at": ms(2026, 7, 7, 6, 40)}).json()
    assert r["work_hours"] == 8.75 and r["overtime_minutes"] == 40
    # a punch-in at 01:00 the next night-shift morning belongs to the previous day
    r = client.post("/attendance/punch-in", json={"emp_code": "EMP0005", "punched_at": ms(2026, 7, 8, 1, 0)}).json()
    assert r["date"] == "2026-07-07"


def test_list_attendance(client, clean):
    for c in ("EMP0002", "EMP0001"):
        emp(client, c)
        for d in (6, 7):
            client.post("/attendance/punch-in", json={"emp_code": c, "punched_at": ms(2026, 7, d, 9, 0)})
    r = client.get("/attendance").json()
    assert [(x["date"], x["emp_code"]) for x in r["items"]] == [
        ("2026-07-07", "EMP0001"), ("2026-07-07", "EMP0002"), ("2026-07-06", "EMP0001"), ("2026-07-06", "EMP0002")]
    assert client.get("/attendance", params={"emp_code": "EMP0001", "date_from": "2026-07-07"}).json()["total"] == 1
    assert client.get("/attendance", params={"date_from": "2026-07-08", "date_to": "2026-07-07"}).status_code == 422
    assert client.get("/attendance", params={"date_from": "2026-02-30"}).status_code == 422
    assert client.get("/attendance", params={"status": "BOGUS"}).status_code == 422
    assert client.get("/attendance", params={"page_size": 2, "page": 2}).json()["items"][0]["date"] == "2026-07-06"


def test_regularize(client, clean):
    emp(client)
    client.post("/attendance/punch-in", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 7, 10, 35)})
    client.post("/attendance/punch-out", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 7, 19, 0)})
    url = "/attendance/EMP0001/2026-07-07"
    body = {"punch_in": ms(2026, 7, 7, 9, 28), "reason": "biometric glitch", "regularized_by": "hr.admin", "late_minutes": 99}
    r = client.patch(url, json=body)
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["late_minutes"] == 0 and b["work_hours"] == 9.53 and len(b["history"]) == 1
    ch = b["history"][0]["changes"]
    assert set(ch) == {"punch_in", "late_minutes", "work_hours"} and ch["late_minutes"] == {"from": 65, "to": 0}
    assert ch["punch_in"]["to"] == ms(2026, 7, 7, 9, 28)
    assert client.patch(url, json=body).status_code == 422  # changes nothing
    r = client.patch(url, json={"status": "LEAVE", "reason": "approved later", "regularized_by": "hr"})
    b = r.json()
    assert b["punch_in"] is None and b["work_hours"] is None and len(b["history"]) == 2
    assert client.patch(url, json={"status": "LEAVE", "punch_in": ms(2026, 7, 7, 9, 0), "reason": "xxxxx", "regularized_by": "h"}).status_code == 422
    assert client.patch(url, json={"status": "PRESENT", "reason": "xxxxx", "regularized_by": "h"}).status_code == 422  # needs punch_in
    assert client.patch(url, json={"punch_in": ms(2026, 7, 8, 9, 0), "status": "PRESENT", "reason": "xxxxx", "regularized_by": "h"}).status_code == 422  # other day
    assert client.patch("/attendance/EMP0001/2026-07-09", json=body).status_code == 404
    assert client.patch("/attendance/NOPE/2026-07-07", json=body).status_code == 404
    assert client.patch(url, json={"reason": "xxxxx", "regularized_by": "h", "status": None}).status_code == 422


def test_concurrent_punch_in_and_out(client, clean):
    emp(client)
    def pin(_): return client.post("/attendance/punch-in", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 6, 9, 0)}).status_code
    with ThreadPoolExecutor(12) as ex:
        codes = list(ex.map(pin, range(12)))
    assert sorted(codes) == [201] + [409] * 11
    def pout(_): return client.post("/attendance/punch-out", json={"emp_code": "EMP0001", "punched_at": ms(2026, 7, 6, 18, 0)}).status_code
    with ThreadPoolExecutor(12) as ex:
        codes = list(ex.map(pout, range(12)))
    assert sorted(codes) == [200] + [409] * 11


def test_health_and_ui(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert "Attendance Console" in client.get("/").text


# ----------------------------- aggregation tests (real MongoDB) ----------------------------- #
def seed_logs(db, rows):
    db.attendance_logs.insert_many([
        {"emp_code": c, "date": d, "status": s, "punch_in": None, "punch_out": None, "work_hours": wh,
         "late_minutes": late, "overtime_minutes": ot, "half_day": hd, "history": []}
        for c, d, s, wh, late, ot, hd in rows])


@needs_mongo
def test_monthly_and_department_summary(client, clean):
    emp(client, "EMP0001", "Eng", joined="2026-01-05")
    emp(client, "EMP0002", "Eng", joined="2026-07-15")   # mid-month joiner
    emp(client, "EMP0003", "Eng", joined="2026-01-05")   # no logs
    emp(client, "EMP0004", "Ops", joined="2026-08-01")   # joins later: Ops omitted in July
    seed_logs(clean, [
        ("EMP0001", "2026-07-06", "PRESENT", 9.0, 0, 0, False),
        ("EMP0001", "2026-07-07", "WFH", 3.5, 20, 40, True),
        ("EMP0001", "2026-07-08", "LEAVE", None, 0, 0, False),
        ("EMP0001", "2026-07-11", "PRESENT", 8.0, 15, 0, False),   # Saturday: no present_days, late still counts
        ("EMP0002", "2026-07-15", "ON_DUTY", 8.0, 0, 0, False),
        ("EMP0002", "2026-07-16", "ABSENT", None, 0, 0, False),
        ("GHOST01", "2026-07-06", "PRESENT", 9.0, 50, 0, False),
    ])
    m = client.get("/analytics/employees/EMP0001/monthly", params={"month": "2026-07"}).json()
    assert m == {"emp_code": "EMP0001", "month": "2026-07", "working_days": 23, "present_days": 1.5, "leave_days": 1,
                 "late_count": 2, "total_late_minutes": 35, "total_overtime_minutes": 40, "attendance_pct": 6.52}
    m = client.get("/analytics/employees/EMP0002/monthly", params={"month": "2026-07"}).json()
    assert m["working_days"] == 13 and m["present_days"] == 1.0 and m["attendance_pct"] == 7.69
    m = client.get("/analytics/employees/EMP0003/monthly", params={"month": "2026-07"}).json()
    assert m["present_days"] == 0 and m["attendance_pct"] == 0.0
    assert client.get("/analytics/employees/EMP0004/monthly", params={"month": "2026-07"}).json()["attendance_pct"] is None
    assert client.get("/analytics/employees/NOPE/monthly", params={"month": "2026-07"}).status_code == 404
    assert client.get("/analytics/employees/EMP0001/monthly", params={"month": "2026-7"}).status_code == 422

    s = client.get("/analytics/departments/summary", params={"month": "2026-07"}).json()
    assert [i["department"] for i in s["items"]] == ["Eng"]
    e = s["items"][0]
    assert e["headcount"] == 3 and e["present_days"] == 2.5 and e["avg_work_hours"] == 7.13  # (9+3.5+8+8)/4
    assert (e["late_count"], e["total_late_minutes"], e["leave_count"], e["on_duty_count"]) == (2, 35, 1, 1)
    assert [i["department"] for i in client.get("/analytics/departments/summary", params={"month": "2026-08"}).json()["items"]] == ["Eng", "Ops"]


@needs_mongo
def test_leaderboard_ties(client, clean):
    for i, d in enumerate(["Eng", "Eng", "Eng", "Eng", "Ops"], 1):
        emp(client, f"EMP000{i}", d)
    seed_logs(clean, [
        ("EMP0001", "2026-07-06", "PRESENT", 8, 50, 0, False),
        ("EMP0002", "2026-07-06", "PRESENT", 8, 30, 0, False),
        ("EMP0003", "2026-07-06", "PRESENT", 8, 30, 0, False),
        ("EMP0004", "2026-07-06", "PRESENT", 8, 20, 0, False),
        ("EMP0005", "2026-07-06", "PRESENT", 8, 0, 0, False),
        ("GHOST01", "2026-07-06", "PRESENT", 8, 99, 0, False),
    ])
    r = client.get("/analytics/leaderboard/late", params={"month": "2026-07", "limit": 2}).json()["items"]
    assert [(x["rank"], x["emp_code"]) for x in r] == [(1, "EMP0001"), (2, "EMP0002"), (2, "EMP0003")]
    r = client.get("/analytics/leaderboard/late", params={"month": "2026-07", "limit": 4}).json()["items"]
    assert [x["rank"] for x in r] == [1, 2, 2, 4]
    r = client.get("/analytics/leaderboard/late", params={"month": "2026-07", "department": "Ops"}).json()["items"]
    assert r == []


@needs_mongo
def test_trend(client, clean):
    emp(client, "EMP0001", "Eng", joined="2026-01-05")
    emp(client, "EMP0002", "Eng", joined="2026-07-09")
    seed_logs(clean, [
        ("EMP0001", "2026-07-06", "PRESENT", 8, 0, 0, False),
        ("EMP0001", "2026-07-07", "PRESENT", 3.5, 20, 0, True),
        ("EMP0001", "2026-07-11", "PRESENT", 8, 0, 0, False),   # Saturday record
    ])
    r = client.get("/analytics/departments/Eng/trend", params={"from": "2026-07-05", "to": "2026-07-12"}).json()["items"]
    assert [x["date"] for x in r] == [f"2026-07-{d:02d}" for d in range(5, 13)]
    sun, mon, tue, wed = r[0], r[1], r[2], r[3]
    assert sun["is_working_day"] is False and sun["attendance_rate"] is None and sun["moving_avg_7d"] is None
    assert mon["attendance_rate"] == 1.0 and tue["attendance_rate"] == 0.5 and tue["moving_avg_7d"] == 0.75
    assert wed["attendance_rate"] == 0.0 and wed["headcount"] == 1 and r[4]["headcount"] == 2
    assert r[6]["present_count"] == 1 and r[6]["attendance_rate"] is None  # Saturday
    assert client.get("/analytics/departments/Nope/trend", params={"from": "2026-07-05", "to": "2026-07-12"}).status_code == 404
    assert client.get("/analytics/departments/Eng/trend", params={"from": "2026-07-12", "to": "2026-07-05"}).status_code == 422
    assert client.get("/analytics/departments/Eng/trend", params={"from": "2026-01-01", "to": "2026-06-01"}).status_code == 422


@needs_mongo
@pytest.mark.parametrize("endpoint,params", [
    ("attendance_list", {}), ("attendance_list", {"emp_code": "EMP0001", "status": "PRESENT"}),
    ("employee_monthly", {"emp_code": "EMP0001", "month": "2026-07"}), ("department_summary", {"month": "2026-07"}),
    ("late_leaderboard", {"month": "2026-07"}), ("department_trend", {"department": "Eng", "from": "2026-07-01", "to": "2026-07-31"})])
def test_explain_uses_index(client, clean, endpoint, params):
    emp(client)
    r = client.get(f"/admin/explain/{endpoint}", params=params)
    assert r.status_code == 200, r.text
    text = r.text
    assert "IXSCAN" in text and "COLLSCAN" not in text
