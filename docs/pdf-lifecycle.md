# PDF Lifecycle and Temporary Storage

## Temporary Storage Policy
Production PDFs from the FAS WUSL website are strictly treated as ephemeral processing artifacts. They are **never** stored permanently in the repository, the database, AWS S3, or any blob storage. Once a PDF has been parsed and its structured data inserted into Neon PostgreSQL, the binary is permanently deleted.

## Safe Temporary Download Process
The download process is handled by `crawler.downloader`.
1. **Size Limit:** Enforces a 20MB limit using chunked/streamed writing. If a file exceeds this, it raises an exception and deletes the partial file.
2. **HTTP Validation:** Raises exceptions for 404s, 500s, and connection timeouts.
3. **Content Validation:** 
    - Rejects responses with a `text/html` Content-Type.
    - Specifically checks the file header bytes for the `%PDF-` signature. Rejects empty or non-PDF binary payloads.

## Lifecycle Coordination
The `managed_pdf_lifecycle` context manager inside `crawler/pdf_lifecycle.py` connects the Downloader, Hasher, and Change Detector.

```python
with managed_pdf_lifecycle(db_session, discovered_doc) as result:
    if result.change_result.status == ChangeStatus.UNCHANGED:
        # PDF is ALREADY deleted by the context manager before yielding.
        pass
    else:
        # PDF is safely available at result.temp_path for the parser.
        parse_pdf(result.temp_path)
# PDF is automatically deleted here by the context manager's finally block.
```

## Cleanup Guarantees
The system uses standard Python `try...finally` resource guarantees.
- **SUCCESS:** The temporary PDF is deleted after the `with` block ends.
- **FAILURE:** If the PDF parser crashes, raises an exception, or is killed, the `finally` block executes and deletes the PDF.
- **UNCHANGED:** If the `ChangeDetector` signals that the SHA-256 hash matches the database, the PDF is deleted immediately (before yielding back to the caller).

## Future Integration
This abstraction allows the future **GitHub Actions Ingestion Worker** to safely map over discovered URLs, safely pull them to the runner's ephemeral disk, pass them to our existing `parser/src` pipeline, and let them be cleaned up with zero disk leak.
