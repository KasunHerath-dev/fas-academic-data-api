import os
import tempfile
import requests
import logging

logger = logging.getLogger(__name__)

TIMEOUT = 10
MAX_DOWNLOAD_SIZE = 20 * 1024 * 1024  # 20 MB max
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

class DownloadException(Exception):
    pass

def validate_pdf_magic_bytes(file_path: str) -> bool:
    """Check if the downloaded file actually begins with %PDF-"""
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
            return header == b"%PDF-"
    except Exception:
        return False

def download_temporary_pdf(url: str) -> str:
    """
    Downloads a PDF securely into a temporary file.
    Returns the absolute path to the temporary file.
    Caller is responsible for cleaning up the file if this succeeds.
    Raises DownloadException on failure.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_path = temp_file.name

    try:
        with session.get(url, stream=True, timeout=TIMEOUT) as response:
            response.raise_for_status()

            # Ensure it's not HTML / checking content-type if provided
            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type.lower():
                raise DownloadException("URL returned HTML instead of PDF content.")

            downloaded_size = 0
            # Read in chunks
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
                    downloaded_size += len(chunk)
                    if downloaded_size > MAX_DOWNLOAD_SIZE:
                        raise DownloadException(f"Download size exceeded maximum allowed limit ({MAX_DOWNLOAD_SIZE} bytes).")
                        
    except Exception as e:
        temp_file.close()
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise DownloadException(f"Failed to download PDF: {str(e)}") from e

    temp_file.close()

    # Validate PDF signature
    if not validate_pdf_magic_bytes(temp_path):
        os.remove(temp_path)
        raise DownloadException("File failed PDF magic-bytes validation.")

    # Reject empty files (magic bytes check already implies at least 5 bytes, but just in case)
    if os.path.getsize(temp_path) < 100: 
        os.remove(temp_path)
        raise DownloadException("Downloaded PDF is too small or empty.")

    return temp_path
