import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    
    # Check basic metadata
    assert schema["info"]["title"] == "FAS Academic Data API"
    assert schema["info"]["version"] == "1.0.0"
    
    # Check description includes some expected keywords
    description = schema["info"]["description"]
    assert "Faculty of Applied Sciences" in description
    assert "read-only" in description.lower()
    
    # Check tags exist
    tags = {tag["name"]: tag for tag in schema.get("tags", [])}
    assert "Health" in tags
    assert "Academic Structure" in tags
    assert "Timetables" in tags
    assert "Academic Calendar" in tags
    assert "Documents" in tags
    assert "Synchronization" in tags
    
    # Check /api/v1 routes exist
    paths = schema.get("paths", {})
    assert "/api/v1/health" in paths
    assert "/api/v1/academic-years" in paths
    assert "/api/v1/timetables" in paths
    assert "/api/v1/timetables/latest" in paths
    assert "/api/v1/calendar" in paths
    assert "/api/v1/calendar/latest" in paths
    assert "/api/v1/documents" in paths
    assert "/api/v1/sync-runs" in paths
    assert "/api/v1/sync-runs/latest" in paths

def test_docs_endpoints():
    # Verify Swagger UI is available
    response = client.get("/docs")
    assert response.status_code == 200
    
    # Verify ReDoc is available
    response = client.get("/redoc")
    assert response.status_code == 200
