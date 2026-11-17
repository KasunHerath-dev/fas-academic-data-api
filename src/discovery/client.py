import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import re
from typing import List, Optional
import sys
import os

# Add parent directory to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discovery.models import DiscoveredDocument

API_BASE = "https://fas.wyb.ac.lk/wp-json/wp/v2"
TIMETABLE_CATEGORY_ID = 54
CALENDAR_CATEGORY_ID = 57

def extract_metadata(title: str) -> dict:
    meta = {
        "document_type": "UNKNOWN",
        "academic_year": None,
        "semester": None,
        "levels": None,
        "revision": "original"
    }
    title_lower = title.lower()
    
    if "re-revised" in title_lower:
        meta["revision"] = "re-revised"
    elif "revised" in title_lower:
        meta["revision"] = "revised"
        
    if "time table" in title_lower or "timetable" in title_lower:
        meta["document_type"] = "TIMETABLE"
    elif "calendar" in title_lower:
        meta["document_type"] = "CALENDAR"
        
    ay_match = re.search(r"(\d{4})[/-](\d{4})", title)
    if ay_match:
        meta["academic_year"] = f"{ay_match.group(1)}/{ay_match.group(2)}"
        
    sem_match = re.search(r"\bSemester\s+([IVX]+)\b", title, re.IGNORECASE)
    if sem_match:
        meta["semester"] = sem_match.group(1).upper()
        
    level_match = re.search(r"\bLevel\s+([\d,\s&]+)", title, re.IGNORECASE)
    
    # Check link text separately if it is provided via an argument or pattern.
    # Actually, we can just find ALL level occurrences and take the LAST one, 
    # since we appended link text to the end of the combined_title.
    matches = list(re.finditer(r"\bLevel\s+([\d,\s&]+)", title, re.IGNORECASE))
    if matches:
        last_match = matches[-1]
        level_str = last_match.group(1)
        levels = [str(digit) for digit in re.findall(r"\d", level_str) if digit != '0']
        if levels:
            meta["levels"] = sorted(list(set(levels)))
            
    return meta

def extract_pdf_links(html_content: str) -> List[dict]:
    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            links.append({
                "url": href,
                "text": a.get_text(strip=True) or href.split("/")[-1]
            })
    return links

class WordPressClient:
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        
    def discover_documents(self) -> List[DiscoveredDocument]:
        documents = []
        page = 1
        
        while True:
            res = self.client.get(
                f"{API_BASE}/posts",
                params={
                    "categories": f"{TIMETABLE_CATEGORY_ID},{CALENDAR_CATEGORY_ID}",
                    "per_page": 20,
                    "page": page
                }
            )
            
            if res.status_code == 400: # Exceeded pages
                break
                
            res.raise_for_status()
            posts = res.json()
            
            if not posts:
                break
                
            for post in posts:
                notice_url = post["link"]
                published_at = datetime.fromisoformat(post["date_gmt"]).replace(tzinfo=timezone.utc)
                modified_at = datetime.fromisoformat(post["modified_gmt"]).replace(tzinfo=timezone.utc)
                
                content_html = post["content"]["rendered"]
                pdf_links = extract_pdf_links(content_html)
                
                # Try to use post title
                post_title = BeautifulSoup(post["title"]["rendered"], "html.parser").get_text(strip=True)
                
                for link in pdf_links:
                    # If multiple PDFs, link text might have level-specific info. We merge it with post title to be safe.
                    combined_title = f"{post_title} {link['text']}"
                    meta = extract_metadata(combined_title)
                    
                    if meta["document_type"] == "UNKNOWN":
                        # Determine by category if title matching failed
                        categories = post.get("categories", [])
                        if TIMETABLE_CATEGORY_ID in categories:
                            meta["document_type"] = "TIMETABLE"
                        elif CALENDAR_CATEGORY_ID in categories:
                            meta["document_type"] = "CALENDAR"
                            
                    doc = DiscoveredDocument(
                        source_url=link["url"],
                        notice_url=notice_url,
                        title=combined_title,
                        document_type=meta["document_type"],
                        academic_year=meta["academic_year"],
                        semester=meta["semester"],
                        levels=meta["levels"],
                        revision=meta["revision"],
                        published_at=published_at,
                        modified_at=modified_at
                    )
                    documents.append(doc)
            
            total_pages = int(res.headers.get("X-WP-TotalPages", 1))
            if page >= total_pages:
                break
                
            page += 1
            
        return documents

if __name__ == "__main__":
    client = WordPressClient()
    docs = client.discover_documents()
    print(f"Discovered {len(docs)} documents.")
    for d in docs[:5]:
        print(d.model_dump_json(indent=2))
