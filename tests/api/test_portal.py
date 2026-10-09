import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_developer_portal():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "FAS Academic Data API" in response.text
    assert "Developer Portal" in response.text
    assert "Read-Only" in response.text
    assert "GitHub Actions" in response.text

def test_portal_endpoints_listed():
    response = client.get("/")
    assert response.status_code == 200
    assert "/api/v1/health" in response.text
    assert "/api/v1/timetables" in response.text
    assert "/api/v1/academic-years" in response.text
    assert "/api/v1/semesters" in response.text
