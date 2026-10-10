"""Integration tests need MongoDB:  MONGO_URI=... MONGO_DB=attendance_test pytest
Set ATTENDANCE_TEST_MOCK=1 to run the CRUD tests on mongomock (aggregation tests are skipped: mongomock
cannot execute $setWindowFields / $densify / $documents)."""
import os

import pytest

MOCK = os.getenv("ATTENDANCE_TEST_MOCK") == "1"
if MOCK:
    import mongomock
    import pymongo

    pymongo.MongoClient = mongomock.MongoClient  # must happen before app.main is imported


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app import main

    if not MOCK:
        os.environ.setdefault("MONGO_DB", "attendance_test")
    with TestClient(main.app) as c:
        yield c


@pytest.fixture()
def clean(client):
    from app import main
    main.db.employees.delete_many({})
    main.db.attendance_logs.delete_many({})
    return main.db


needs_mongo = pytest.mark.skipif(MOCK, reason="needs a real MongoDB")
