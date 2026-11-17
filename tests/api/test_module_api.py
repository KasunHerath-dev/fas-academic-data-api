import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.dependencies.database import get_db
from api.main import app
from database.database import Base
from database.models.models import Document, TimetableSession

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
SessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    doc = Document(title="L2&3", document_type="TIMETABLE", academic_year="2024/2025", semester="I",
                   level="2,3", revision="revised", sha256="x", status="processed", validation_status="SAFE")
    db.add(doc)
    db.flush()
    common = dict(document_id=doc.id, academic_year="2024/2025", semester="I", level="2,3",
                  time_source="explicit", verification_status="verified")
    db.add_all([
        # Stored before the module matcher existed: damaged code, no raw copy
        TimetableSession(day="Monday", start_time="08:30", end_time="10:30", module_code="MIS 4142",
                         class_type="L", **common),
        TimetableSession(day="Monday", start_time="10:30", end_time="12:30", module_code="IMGT 3+34",
                         class_type="P", **common),
        # Stored by the fixed pipeline
        TimetableSession(day="Tuesday", start_time="08:30", end_time="10:30", module_code="CMIS 3114",
                         raw_module_code="CMIS 3114", class_type="L", **common),
    ])
    db.commit()
    db.close()

    def override():
        s = SessionLocal()
        try:
            yield s
        finally:
            s.close()

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    if previous:
        app.dependency_overrides[get_db] = previous
    else:
        app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


def test_sessions_are_enriched_and_damaged_codes_repaired(client):
    data = client.get("/api/v1/timetables").json()["data"]
    by_raw = {s["raw_module_code"]: s for s in data}

    image = by_raw["MIS 4142"]
    assert image["module_code"] == "CMIS 4142"
    assert image["module_name"] == "Image Processing"
    assert image["credits"] == 2
    assert image["subject"] == "CMIS"
    assert image["session_type"] == "L"  # was always null: schema read a field the model lacks
    assert image["module_match"]["status"] == "normalized"

    lab = by_raw["IMGT 3+34"]
    assert lab["module_code"] == "IMGT 3†34"
    assert lab["year_long"] is True
    assert lab["module_match"]["catalogue_confirmed"] is False

    assert by_raw["CMIS 3114"]["module_name"] == "Data Communication & Computer Networks"


def test_sessions_are_ordered_by_weekday(client):
    days = [s["day"] for s in client.get("/api/v1/timetables").json()["data"]]
    assert days == ["Monday", "Monday", "Tuesday"]


def test_module_code_filter_accepts_ocr_variants(client):
    for query in ("IMGT 3+34", "IMGT 3ᵻ34", "IMGT 3†34"):
        res = client.get("/api/v1/timetables", params={"module_code": query}).json()
        assert res["count"] == 1, query


def test_level_filter_matches_combined_timetables(client):
    assert client.get("/api/v1/timetables?level=2").json()["count"] == 3
    assert client.get("/api/v1/timetables?level=3").json()["count"] == 3
    assert client.get("/api/v1/timetables?level=1").json()["count"] == 0


def test_semester_filter_accepts_numeric_and_roman(client):
    assert client.get("/api/v1/timetables?semester=1").json()["count"] == 3
    assert client.get("/api/v1/timetables?semester=I").json()["count"] == 3
    assert client.get("/api/v1/timetables?semester=2").json()["count"] == 0


def test_latest_timetable_resolves_combined_level_and_semester_forms(client):
    res = client.get("/api/v1/timetables/latest?academic_year=2024/2025&semester=1&level=3")
    assert res.status_code == 200
    assert res.json()["count"] == 3


def test_subject_filter(client):
    assert client.get("/api/v1/timetables?subject=imgt").json()["count"] == 1


def test_catalogue_modules_endpoint(client):
    res = client.get("/api/v1/catalogue/modules?level=4&semester=1&subject=CMIS")
    assert res.status_code == 200
    codes = [m["code"] for m in res.json()]
    assert "CMIS 4142" in codes and "CMIS 4†18" in codes
    assert "CMIS 4216" not in codes


def test_resolve_endpoint(client):
    res = client.get("/api/v1/catalogue/modules/resolve", params={"code": "MIS 4142"})
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == "CMIS 4142"
    assert body["module"]["title"] == "Image Processing"

    assert client.get("/api/v1/catalogue/modules/resolve", params={"code": "hello"}).status_code == 404


def test_api_never_emits_needs_review_for_english_courses(client):
    db = SessionLocal()
    doc_id = db.query(TimetableSession).first().document_id
    db.add(TimetableSession(document_id=doc_id, academic_year="2024/2025", semester="I", level="1",
                            day="Wednesday", start_time="13:00", end_time="15:00", module_code="ELPC 1+10",
                            time_source="explicit", verification_status="verified"))
    db.commit()
    db.close()
    for query in ("ELPC I", "ELPC 1+10", "elpc i"):
        res = client.get("/api/v1/timetables", params={"module_code": query}).json()
        assert res["count"] == 1, query
    s = res["data"][0]
    assert s["module_code"] == "ELPC I"
    assert s["raw_module_code"] == "ELPC 1+10"
    assert s["module_name"] == "English Language Proficiency Course I"
    assert s["subject"] == "ELPC"
    assert s["non_credit"] is True
    assert s["credits"] == 0
    assert s["year_long"] is True
    assert s["verification_status"] == "verified"
    assert "NEEDS_REVIEW" not in str(s)
