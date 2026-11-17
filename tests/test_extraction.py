import pytest
import os
import respx
import httpx
from extraction.pdf_utils import download_pdf, verify_pdf_readability

@respx.mock
def test_download_valid_pdf():
    pdf_content = b"%PDF-1.4\n%EOF\n"
    respx.get("http://example.com/test.pdf").respond(
        content=pdf_content,
        headers={"Content-Type": "application/pdf"},
        status_code=200
    )
    
    path, sha = download_pdf("http://example.com/test.pdf")
    
    assert path is not None
    assert sha is not None
    assert os.path.exists(path)
    
    with open(path, "rb") as f:
        assert f.read() == pdf_content
        
    os.remove(path)

@respx.mock
def test_download_invalid_pdf():
    respx.get("http://example.com/test.html").respond(
        content=b"<html></html>",
        headers={"Content-Type": "text/html"},
        status_code=200
    )
    
    path, sha = download_pdf("http://example.com/test.html")
    
    assert path is None
    assert sha is None
