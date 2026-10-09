"""
Tests for source_discovery.get_post_metadata().

Verifies:
  1. published_at extracted from <time> element only.
  2. source_updated_at extracted from article:modified_time OGP only, independently.
  3. Both dates present when source provides distinct values.
  4. Both None when no date metadata present.
  5. HTTP Last-Modified used for source_updated_at only when genuinely distinct from published_at.
  6. published_at never copied into source_updated_at.
"""
import pytest
from datetime import datetime, timezone, timedelta
from crawler.source_discovery import SourceDiscovery


@pytest.fixture
def sd():
    return SourceDiscovery()


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def wp_page(time_text="", modified_meta=""):
    """Build a minimal WordPress-style HTML page."""
    time_tag = f"<time>{time_text}</time>" if time_text else ""
    mod_meta = f'<meta property="article:modified_time" content="{modified_meta}" />' if modified_meta else ""
    return f"""
    <html><head>{mod_meta}</head>
    <body><main>{time_tag}<p>Some content.</p></main></body>
    </html>
    """


# ---------------------------------------------------------------------------
# Test 1: publication date only
# ---------------------------------------------------------------------------

def test_publication_date_only(sd):
    """<time> present — published_at extracted; source_updated_at is None."""
    html = wp_page(time_text="July 30, 2026")
    pub, upd = sd.get_post_metadata(html, headers=None)
    assert pub == datetime(2026, 7, 30, tzinfo=timezone.utc)
    assert upd is None, "source_updated_at must be None when no modification date available"


# ---------------------------------------------------------------------------
# Test 2: distinct publication and modification dates
# ---------------------------------------------------------------------------

def test_distinct_publication_and_modification_dates(sd):
    """OGP article:modified_time present — yields independent source_updated_at."""
    html = wp_page(
        time_text="July 30, 2026",
        modified_meta="2026-09-10T08:00:00+00:00",
    )
    pub, upd = sd.get_post_metadata(html, headers=None)
    assert pub == datetime(2026, 7, 30, tzinfo=timezone.utc)
    assert upd == datetime(2026, 9, 10, 8, 0, 0, tzinfo=timezone.utc)
    assert pub != upd, "published_at and source_updated_at must be independent values"


# ---------------------------------------------------------------------------
# Test 3: no date metadata at all
# ---------------------------------------------------------------------------

def test_no_date_metadata(sd):
    """No <time> and no OGP meta — both fields are None."""
    html = "<html><body><p>No dates here.</p></body></html>"
    pub, upd = sd.get_post_metadata(html, headers=None)
    assert pub is None
    assert upd is None


# ---------------------------------------------------------------------------
# Test 4: HTTP Last-Modified only (no HTML dates)
# ---------------------------------------------------------------------------

def test_http_last_modified_only(sd):
    """HTTP Last-Modified with no HTML publication date populates source_updated_at only."""
    html = "<html><body><p>No HTML dates.</p></body></html>"
    headers = {"Last-Modified": "Wed, 10 Sep 2026 08:00:00 GMT"}
    pub, upd = sd.get_post_metadata(html, headers=headers)
    assert pub is None, "No <time> tag means published_at must be None"
    assert upd == datetime(2026, 9, 10, 8, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Test 5: HTTP Last-Modified same as published_at — should NOT set source_updated_at
# ---------------------------------------------------------------------------

def test_http_last_modified_same_as_published_not_used(sd):
    """Last-Modified within 60 s of published_at — not treated as independent modification."""
    # published_at = 2026-07-30 00:00:00 UTC (from <time>)
    # Last-Modified = 2026-07-30 00:00:30 UTC (only 30 s later — within threshold)
    html = wp_page(time_text="July 30, 2026")
    headers = {"Last-Modified": "Thu, 30 Jul 2026 00:00:30 GMT"}
    pub, upd = sd.get_post_metadata(html, headers=headers)
    assert pub == datetime(2026, 7, 30, tzinfo=timezone.utc)
    assert upd is None, (
        "Last-Modified within 60 s of published_at must not be treated as independent modification"
    )


# ---------------------------------------------------------------------------
# Test 6: published_at must never be copied into source_updated_at
# ---------------------------------------------------------------------------

def test_published_at_never_copied_to_source_updated_at(sd):
    """Even when modified_time is absent, source_updated_at stays None — not a copy of published_at."""
    for time_text in ("July 30, 2026", "September 10, 2026", "October 05, 2026"):
        html = wp_page(time_text=time_text)
        pub, upd = sd.get_post_metadata(html, headers=None)
        assert pub is not None, f"published_at should parse from '{time_text}'"
        assert upd is None, (
            f"source_updated_at must be None, not a copy of published_at={pub}"
        )
