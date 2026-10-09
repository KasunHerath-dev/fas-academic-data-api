import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
import logging

from crawler.models import DiscoveredDocument
from crawler.metadata_extractor import extract_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

class SourceDiscovery:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def fetch_page(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return ""

    def fetch_page_with_headers(self, url: str):
        """Fetch a page and return (html_text, response_headers). Returns ('', {}) on failure."""
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.text, dict(response.headers)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return "", {}

    def get_post_metadata(self, html: str, headers: dict | None = None):
        """
        Extract publication and modification dates from a WordPress post page.

        published_at     — from the <time> element (the post's publication date).
        source_updated_at — from article:modified_time OGP meta tag *only*, or
                            from HTTP Last-Modified header *only* when it is
                            present and differs from published_at by more than
                            60 seconds.  Never derived from published_at itself.

        Returns (published_at, source_updated_at) where either may be None.
        """
        soup = BeautifulSoup(html, "lxml")
        published_at = None
        source_updated_at = None

        # 1. Publication date — WordPress <time> element
        time_tag = soup.find("time")
        if time_tag and time_tag.text:
            try:
                published_at = datetime.strptime(
                    time_tag.text.strip(), "%B %d, %Y"
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                # Some WP themes emit an ISO datetime attribute instead
                dt_attr = time_tag.get("datetime", "")
                if dt_attr:
                    try:
                        published_at = datetime.fromisoformat(dt_attr).replace(tzinfo=timezone.utc)
                    except ValueError:
                        pass

        # 2. Modification date — article:modified_time OGP meta (a distinct field from published_time)
        mod_meta = soup.find("meta", property="article:modified_time")
        if mod_meta and mod_meta.get("content"):
            try:
                source_updated_at = datetime.fromisoformat(
                    mod_meta["content"]
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        # 3. Fallback: HTTP Last-Modified header (only when provided and genuinely distinct)
        if source_updated_at is None and headers:
            last_modified_str = headers.get("Last-Modified", "")
            if last_modified_str:
                try:
                    from email.utils import parsedate_to_datetime
                    lm = parsedate_to_datetime(last_modified_str).replace(tzinfo=timezone.utc)
                    # Only use when it differs meaningfully from the publication date
                    if published_at is None or abs((lm - published_at).total_seconds()) > 60:
                        source_updated_at = lm
                except Exception:
                    pass

        # source_updated_at stays None when no independently verified modification
        # date is available — it is NEVER copied from published_at.
        return published_at, source_updated_at

    def get_pdf_link_from_post(self, post_url: str):
        """
        Fetch a WordPress post page, extract the first PDF link, published_at,
        and source_updated_at.  Returns ('', None, None) on failure.
        """
        html, headers = self.fetch_page_with_headers(post_url)
        if not html:
            return "", None, None

        published_at, source_updated_at = self.get_post_metadata(html, headers)
        soup = BeautifulSoup(html, "lxml")
        content_area = soup.find("main") or soup.find("div", class_="entry-content") or soup.body
        if not content_area:
            return "", published_at, source_updated_at
        for a_tag in content_area.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.lower().endswith(".pdf"):
                return urljoin(post_url, href), published_at, source_updated_at
        return "", published_at, source_updated_at

    def discover_documents(self, source_url: str) -> list[DiscoveredDocument]:
        html = self.fetch_page(source_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        discovered = []
        seen_urls = set()

        content_area = soup.find("main") or soup.find("div", class_="entry-content") or soup.body

        if not content_area:
            return []

        for a_tag in content_area.find_all("a", href=True):
            href = a_tag["href"].strip()

            absolute_url = urljoin(source_url, href)
            absolute_url = absolute_url.split("#")[0]

            if not absolute_url or absolute_url == source_url or absolute_url == source_url.rstrip("/"):
                continue

            if absolute_url in seen_urls:
                continue

            seen_urls.add(absolute_url)

            link_text = a_tag.get_text(strip=True)
            if not link_text:
                link_text = absolute_url.split("/")[-1]

            if "read more" in link_text.lower():
                continue

            published_at = None
            source_updated_at = None

            # If the link itself is a PDF, use it directly
            if absolute_url.lower().endswith(".pdf"):
                pdf_url = absolute_url
                post_url = source_url
            else:
                # It should be a post page — skip obvious non-post links
                if "/category/" in absolute_url.lower() or "/tag/" in absolute_url.lower() or "/author/" in absolute_url.lower():
                    continue

                pdf_url, published_at, source_updated_at = self.get_pdf_link_from_post(absolute_url)
                post_url = absolute_url

            if not pdf_url:
                continue

            title = link_text
            meta = extract_metadata(title)

            # Skip examination timetables
            if "exam" in title.lower():
                continue

            # Skip documents with unrecognised type
            if meta["document_type"] == "unknown":
                continue

            doc = DiscoveredDocument(
                source_url=pdf_url,
                source_page_url=post_url,
                title=title,
                link_text=link_text,
                document_type=meta["document_type"],
                academic_year=meta["academic_year"],
                semester=meta["semester"],
                levels=meta.get("levels"),
                major=meta.get("major"),
                programme=meta.get("programme"),
                revision=meta["revision"],
                published_at=published_at,
                source_updated_at=source_updated_at,
                discovered_at=datetime.now(timezone.utc),
            )
            discovered.append(doc)

        return discovered
