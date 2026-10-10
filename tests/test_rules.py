"""Pure unit tests for business rules R1-R5, R8 (no MongoDB needed):  pytest tests/test_rules.py"""
from datetime import datetime, timezone, timedelta

from app import main as m

IST = m.IST


def ist(y, mo, d, h, mi, s=0):
    return datetime(y, mo, d, h, mi, s, tzinfo=IST).astimezone(timezone.utc)


DAY = {"shift_start": "09:30", "shift_end": "18:30"}
NIGHT = {"shift_start": "22:00", "shift_end": "06:00"}


def test_late_grace_boundaries():  # R2
    d = "2026-07-06"
    assert m.compute_late_minutes(ist(2026, 7, 6, 9, 40, 0), d, "09:30") == 0
    assert m.compute_late_minutes(ist(2026, 7, 6, 9, 40, 1), d, "09:30") == 10
    assert m.compute_late_minutes(ist(2026, 7, 6, 10, 15, 59), d, "09:30") == 45
    assert m.compute_late_minutes(ist(2026, 7, 6, 9, 0, 0), d, "09:30") == 0  # early


def test_overtime_minimum_30():  # R3
    d = "2026-07-06"
    assert m.compute_overtime(ist(2026, 7, 6, 18, 59, 59), d, "09:30", "18:30") == 0
    assert m.compute_overtime(ist(2026, 7, 6, 19, 0, 0), d, "09:30", "18:30") == 30
    assert m.compute_overtime(ist(2026, 7, 6, 19, 10, 0), d, "09:30", "18:30") == 40
    assert m.compute_overtime(ist(2026, 7, 6, 18, 35, 0), d, "09:30", "18:30") == 0


def test_work_hours_half_up():  # R4
    a = ist(2026, 7, 6, 9, 0, 0)
    assert m.compute_work_hours(a, a + timedelta(seconds=32820)) == 9.12
    assert m.compute_work_hours(a, a + timedelta(seconds=int(3600 * 4.125))) == 4.13  # 4.125 -> half-up
    assert m.compute_work_hours(a, a + timedelta(seconds=int(3600 * 0.005))) == 0.01  # 18s -> 0.005


def test_half_day_uses_rounded_hours():  # R5
    emp = {**DAY}
    a = ist(2026, 7, 6, 9, 30, 0)
    # 4.495h = 16182s -> rounds to 4.50 -> NOT a half day
    assert m.derive(emp, "2026-07-06", a, a + timedelta(seconds=16182))["half_day"] is False
    # 4.49h = 16164s -> 4.49 -> half day
    assert m.derive(emp, "2026-07-06", a, a + timedelta(seconds=16164))["half_day"] is True


def test_overnight_date_and_overtime():  # R1
    p_in = ist(2026, 7, 6, 21, 55)
    assert m.attendance_date(p_in, "22:00", "06:00") == "2026-07-06"
    early = ist(2026, 7, 7, 1, 30)  # after midnight: belongs to the shift that started on the 6th
    assert m.attendance_date(early, "22:00", "06:00") == "2026-07-06"
    assert m.attendance_date(ist(2026, 7, 7, 6, 0, 0), "22:00", "06:00") == "2026-07-07"  # not earlier than end
    out = ist(2026, 7, 7, 6, 40)
    assert m.compute_overtime(out, "2026-07-06", "22:00", "06:00") == 40
    assert m.compute_late_minutes(early, "2026-07-06", "22:00") == 210


def test_ist_date_not_utc_date():  # R1
    # 00:10 IST on the 7th is still the 6th in UTC
    assert m.attendance_date(ist(2026, 7, 7, 0, 10), "09:30", "18:30") == "2026-07-07"


def test_ms_conversion_truncates_seconds():
    dt = m.ms_to_dt(1783312500999)
    assert dt.microsecond == 0 and m.dt_to_ms(dt) == 1783312500000


def test_half_up_rounding():  # R8
    assert m.half_up(0.12345, 4) == 0.1235
    assert m.half_up(2.675, 2) == 2.68
    assert m.half_up(8.125, 2) == 8.13
    assert m.half_up(None, 2) is None


def test_working_days_and_month_bounds():  # R7
    first, last = m.month_bounds("2026-07")
    assert (first.isoformat(), last.isoformat()) == ("2026-07-01", "2026-07-31")
    assert m.working_days("2026-01-05", first, last) == 23
    assert m.working_days("2026-07-15", first, last) == 13  # Wed 15 .. Fri 31
    assert m.working_days("2026-08-01", first, last) == 0
    assert m.month_bounds("2026-12")[1].isoformat() == "2026-12-31"
