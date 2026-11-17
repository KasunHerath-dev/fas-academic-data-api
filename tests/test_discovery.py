import pytest
import respx
import httpx
from datetime import datetime, timezone
from discovery.client import WordPressClient, API_BASE

@respx.mock
def test_discovery_pagination_and_multiple_pdfs():
    # Mock first page
    respx.get(
        f"{API_BASE}/posts",
        params={"categories": "54,57", "per_page": "20", "page": "1"}
    ).respond(
        json=[
            {
                "link": "https://fas.wyb.ac.lk/notice1/",
                "date_gmt": "2024-01-01T10:00:00",
                "modified_gmt": "2024-01-01T10:05:00",
                "title": {"rendered": "Academic Time Table \u2013 Level 1 & 2 Semester I"},
                "content": {"rendered": '<a href="http://example.com/l1.pdf">Level 1</a> <a href="http://example.com/l2.pdf">Level 2</a>'},
                "categories": [54]
            }
        ],
        headers={"X-WP-TotalPages": "2"},
        status_code=200
    )

    # Mock second page
    respx.get(
        f"{API_BASE}/posts",
        params={"categories": "54,57", "per_page": "20", "page": "2"}
    ).respond(
        json=[
            {
                "link": "https://fas.wyb.ac.lk/notice2/",
                "date_gmt": "2024-02-01T10:00:00",
                "modified_gmt": "2024-02-01T10:05:00",
                "title": {"rendered": "Revised Academic Calendar 2024/2025"},
                "content": {"rendered": '<a href="http://example.com/cal.pdf">Download</a>'},
                "categories": [57]
            }
        ],
        headers={"X-WP-TotalPages": "2"},
        status_code=200
    )

    client = WordPressClient()
    docs = client.discover_documents()
    
    assert len(docs) == 3

    assert docs[0].source_url == "http://example.com/l1.pdf"
    assert docs[0].levels == ["1"]
    assert docs[0].document_type == "TIMETABLE"
    assert docs[0].revision == "original"

    assert docs[1].source_url == "http://example.com/l2.pdf"
    assert docs[1].levels == ["2"]
    assert docs[1].document_type == "TIMETABLE"
    
    assert docs[2].source_url == "http://example.com/cal.pdf"
    assert docs[2].academic_year == "2024/2025"
    assert docs[2].document_type == "CALENDAR"
    assert docs[2].revision == "revised"
