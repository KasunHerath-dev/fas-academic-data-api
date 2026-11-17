import hashlib
import os
import tempfile
import httpx
from typing import Optional, Tuple
import pymupdf # PyMuPDF
import pdfplumber

def download_pdf(url: str, timeout: int = 30) -> Tuple[Optional[str], Optional[str]]:
    """
    Downloads a PDF from a URL to a temporary file.
    Returns (temp_file_path, sha256_hash). Returns (None, None) on failure.
    Caller is responsible for deleting the temp file.
    """
    try:
        with httpx.Client(timeout=timeout) as client:
            res = client.get(url, follow_redirects=True)
            res.raise_for_status()
            
            content_type = res.headers.get("Content-Type", "")
            if "application/pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
                # Warning: Might not be a PDF, but we'll try parsing it anyway
                pass
                
            content = res.content
            if not content.startswith(b"%PDF"):
                return None, None
                
            sha256_hash = hashlib.sha256(content).hexdigest()
            
            fd, path = tempfile.mkstemp(suffix=".pdf")
            with os.fdopen(fd, "wb") as f:
                f.write(content)
                
            return path, sha256_hash
    except Exception:
        return None, None

def verify_pdf_readability(file_path: str) -> bool:
    try:
        with pymupdf.open(file_path) as doc:
            if doc.is_encrypted:
                return False
            if len(doc) == 0:
                return False
            return True
    except Exception:
        return False
