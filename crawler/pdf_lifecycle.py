import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy.orm import Session

from crawler.models import DiscoveredDocument
from crawler.hasher import calculate_sha256
from crawler.change_detector import ChangeDetector, ChangeStatus, ChangeResult
from crawler.downloader import download_temporary_pdf, DownloadException

logger = logging.getLogger(__name__)

class LifecycleResult:
    def __init__(self, temp_path: Optional[str], change_result: Optional[ChangeResult], error: Optional[str] = None, sha256: Optional[str] = None):
        self.temp_path = temp_path
        self.change_result = change_result
        self.error = error
        self.sha256 = sha256

@contextmanager
def managed_pdf_lifecycle(db_session: Session, discovered_doc: DiscoveredDocument) -> Generator[LifecycleResult, None, None]:
    """
    Context manager that safely downloads, hashes, and detects changes for a discovered document.
    Yields the LifecycleResult.
    If the document is UNCHANGED, the temp file is deleted BEFORE yielding, and temp_path is None.
    If NEW or CHANGED, yields the temp file path for the caller to parse, then deletes it automatically afterward.
    Guarantees cleanup on success or exception.
    """
    temp_path = None
    try:
        # Step 1: Download
        try:
            temp_path = download_temporary_pdf(discovered_doc.source_url)
        except DownloadException as e:
            yield LifecycleResult(temp_path=None, change_result=None, error=str(e))
            return
            
        # Step 2: Hash
        try:
            sha256_hash = calculate_sha256(temp_path)
        except Exception as e:
            yield LifecycleResult(temp_path=None, change_result=None, error=f"Hashing failed: {str(e)}")
            return
            
        # Step 3: Detect Changes
        try:
            detector = ChangeDetector(db_session)
            change_result = detector.detect(discovered_doc, sha256_hash)
        except Exception as e:
            yield LifecycleResult(temp_path=None, change_result=None, error=f"Change detection failed: {str(e)}")
            return
            
        # Step 4: Act on result
        if change_result.status == ChangeStatus.UNCHANGED:
            # Delete it immediately, we don't need to parse it
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
                temp_path = None
            yield LifecycleResult(temp_path=None, change_result=change_result, sha256=sha256_hash)
        else:
            # NEW or CHANGED -> let the caller process it
            yield LifecycleResult(temp_path=temp_path, change_result=change_result, sha256=sha256_hash)

    finally:
        # Step 5: Guaranteed cleanup
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.error(f"Failed to delete temporary PDF at {temp_path}: {e}")
