"""Discovery of the latest documents through the FAS WordPress REST API."""
import re

import pytest
import requests_mock as rm

from crawler.metadata_extractor import extract_metadata, extract_revision
from crawler.source_discovery import (
    CALENDAR_URL,
    SourceDiscovery,
    TIMETABLE_URL,
    WP_API_BASE,
)

POSTS_URL = re.compile(re.escape(f"{WP_API_BASE}/posts"))


def _post(title, links, date="2026-09-10T08:00:00", modified="2026-10-05T09:30:00", categories=(54,)):
    content = " ".join(f'<a href="{href}">{text}</a>' for href, text in links)
    return {
        "link": "https://fas.wyb.ac.lk/notice/",
        "date_gmt": date,
        "modified_gmt": modified,
        "title": {"rendered": title},
        "content": {"rendered": f"<p>{content}</p>"},
        "categories": list(categories),
    }


def test_wordpress_api_splits_multi_pdf_notice_by_level():
    posts = [_post(
        "Revised &#8211; Academic Time Table &#8211; Semester I (Academic Year 2024/2025)",
        [("https://fas.wyb.ac.lk/wp-content/uploads/L1.pdf", "Level 1"),
         ("https://fas.wyb.ac.lk/wp-content/uploads/L23.pdf", "Level 2 & 3"),
         ("https://fas.wyb.ac.lk/wp-content/uploads/L1.pdf", "Level 1 (duplicate link)"),
         ("https://fas.wyb.ac.lk/other/page", "not a pdf")],
    )]
    with rm.Mocker() as m:
        m.get(POSTS_URL, json=posts, headers={"X-WP-TotalPages": "1"})
        docs = SourceDiscovery().discover_from_wordpress_api()

    assert [d.source_url.rsplit("/", 1)[-1] for d in docs] == ["L1.pdf", "L23.pdf"]
    assert docs[0].levels == [1]
    assert docs[1].levels == [2, 3]
    for d in docs:
        assert d.document_type == "TIMETABLE"
        assert d.academic_year == "2024/2025"
        assert d.semester == "I"
        assert d.revision == "revised"
        assert d.published_at is not None and d.source_updated_at is not None


def test_wordpress_api_paginates_and_uses_category_when_title_is_vague():
    page1 = [_post("Time Table Level 4 Semester I 2024/2025", [("https://x/l4.pdf", "Download")])]
    page2 = [_post("Notice 2024/2025", [("https://x/cal.pdf", "Download")], categories=(57,))]
    with rm.Mocker() as m:
        m.get(POSTS_URL, [
            {"json": page1, "headers": {"X-WP-TotalPages": "2"}},
            {"json": page2, "headers": {"X-WP-TotalPages": "2"}},
        ])
        docs = SourceDiscovery().discover_from_wordpress_api()
        assert m.call_count == 2
        assert m.request_history[0].qs["orderby"] == ["modified"]

    assert [d.document_type for d in docs] == ["TIMETABLE", "ACADEMIC_CALENDAR"]


def test_exam_timetables_are_skipped():
    posts = [_post("Examination Time Table Level 1 2024/2025", [("https://x/exam.pdf", "Level 1")])]
    with rm.Mocker() as m:
        m.get(POSTS_URL, json=posts, headers={"X-WP-TotalPages": "1"})
        assert SourceDiscovery().discover_from_wordpress_api() == []


def test_discover_all_falls_back_to_html_when_api_fails():
    listing = '<html><body><main><a href="https://x/l2.pdf">Academic Time Table – Level 2 Semester I (2024/2025)</a></main></body></html>'
    with rm.Mocker() as m:
        m.get(POSTS_URL, status_code=404)
        m.get(TIMETABLE_URL, text=listing)
        m.get(CALENDAR_URL, text="<html><body><main></main></body></html>")
        docs = SourceDiscovery().discover_all()

    assert [d.source_url for d in docs] == ["https://x/l2.pdf"]
    assert docs[0].levels == [2]


def test_discover_all_returns_newest_first_and_dedupes():
    posts = [
        _post("Academic Time Table Level 1 Semester I 2023/2024", [("https://x/old.pdf", "Level 1")],
              date="2024-01-01T00:00:00", modified="2024-01-01T00:00:00"),
        _post("Revised 02 Academic Time Table Level 1 Semester I 2024/2025", [("https://x/new.pdf", "Level 1")],
              date="2026-10-05T00:00:00", modified="2026-10-05T00:00:00"),
        _post("Academic Time Table Level 1 Semester I 2023/2024", [("https://x/old.pdf", "Level 1")]),
    ]
    with rm.Mocker() as m:
        m.get(POSTS_URL, json=posts, headers={"X-WP-TotalPages": "1"})
        docs = SourceDiscovery().discover_all()

    assert [d.source_url for d in docs] == ["https://x/new.pdf", "https://x/old.pdf"]
    assert docs[0].revision == "revised-2"


def test_html_discovery_skips_unrecognised_documents():
    """Regression: the old check compared document_type with 'unknown' and never matched None."""
    listing = '<html><body><main><a href="https://x/form.pdf">Student registration form</a></main></body></html>'
    with rm.Mocker() as m:
        m.get(TIMETABLE_URL, text=listing)
        assert SourceDiscovery().discover_documents(TIMETABLE_URL) == []


@pytest.mark.parametrize("title, expected", [
    ("Academic Time Table", "original"),
    ("Revised – Academic Time Table", "revised"),
    ("Revised 02 – Academic Time Table", "revised-2"),
    ("2nd Revised Academic Time Table", "revised-2"),
    ("Re-Revised Academic Time Table", "re-revised"),
    ("Re Revised Academic Time Table", "re-revised"),
    ("Revised Time Table 2024/2025", "revised"),
])
def test_revision_numbers(title, expected):
    assert extract_revision(title) == expected


def test_metadata_variants():
    meta = extract_metadata("Academic Time-Table Level 3 Semester 2 (2024/25)")
    assert meta["document_type"] == "TIMETABLE"
    assert meta["semester"] == "II"
    assert meta["academic_year"] == "2024/2025"
    assert meta["levels"] == [3]
