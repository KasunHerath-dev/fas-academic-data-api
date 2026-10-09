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

    def discover_documents(self, source_url: str) -> list[DiscoveredDocument]:
        html = self.fetch_page(source_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        discovered = []
        seen_urls = set()

        # Try to constrain to main content to avoid header/footer noise
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
                
            # Ignore "Read More" links as they usually duplicate the post title links
            if "read more" in link_text.lower():
                continue

            title = link_text 
            meta = extract_metadata(title)
            
            doc = DiscoveredDocument(
                source_url=absolute_url,
                source_page_url=source_url,
                title=title,
                link_text=link_text,
                document_type=meta["document_type"],
                academic_year=meta["academic_year"],
                semester=meta["semester"],
                levels=meta["levels"],
                major=meta["major"],
                programme=meta["programme"],
                revision=meta["revision"],
                discovered_at=datetime.now(timezone.utc)
            )
            discovered.append(doc)

        return discovered
