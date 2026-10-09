import pytest
from unittest.mock import patch, MagicMock
from scripts.run_academic_data_sync import run_dry_run

@patch("scripts.run_academic_data_sync.os.remove")
@patch("scripts.run_academic_data_sync.os.path.exists")
@patch("scripts.run_academic_data_sync.SourceDiscovery")
@patch("scripts.run_academic_data_sync.download_temporary_pdf")
@patch("scripts.run_academic_data_sync.calculate_sha256")
@patch("scripts.run_academic_data_sync.parse_timetable")
@patch("scripts.run_academic_data_sync.TimetableValidator")
@patch("scripts.run_academic_data_sync.SessionLocal")
def test_dry_run_is_fully_isolated(
    mock_session_local,
    mock_validator_class,
    mock_parse,
    mock_calc_hash,
    mock_download,
    mock_discovery_class,
    mock_exists,
    mock_remove
):
    # Setup mocks
    mock_discovery = mock_discovery_class.return_value

    mock_doc = MagicMock()
    mock_doc.title = "Test Doc"
    mock_doc.document_type = "TIMETABLE"
    mock_doc.url = "http://test"
    mock_doc.source_url = "http://test.pdf"

    mock_discovery.discover_documents.return_value = [mock_doc]

    mock_download.return_value = "/tmp/test.pdf"
    mock_calc_hash.return_value = "fakehash"

    mock_validator = mock_validator_class.return_value
    mock_validator.validate_timetable.return_value.status = "REVIEW_REQUIRED"
    mock_validator.validate_timetable.return_value.valid_sessions = 1
    mock_validator.validate_timetable.return_value.uncertain_sessions = 0
    mock_validator.validate_timetable.return_value.invalid_sessions = 0

    mock_exists.return_value = True

    # Run dry run
    run_dry_run()

    # Assertions
    # 1. No database connection
    mock_session_local.assert_not_called()

    # 2. PDF Downloaded and parsed
    mock_download.assert_called_with("http://test.pdf")
    mock_parse.assert_called_with("/tmp/test.pdf")

    # 3. Temp file cleaned up
    mock_remove.assert_called_with("/tmp/test.pdf")

@patch("scripts.run_academic_data_sync.os.remove")
@patch("scripts.run_academic_data_sync.os.path.exists")
@patch("scripts.run_academic_data_sync.SourceDiscovery")
@patch("scripts.run_academic_data_sync.download_temporary_pdf")
@patch("scripts.run_academic_data_sync.SessionLocal")
def test_dry_run_cleans_up_on_failure(
    mock_session_local,
    mock_download,
    mock_discovery_class,
    mock_exists,
    mock_remove
):
    mock_discovery = mock_discovery_class.return_value
    mock_doc = MagicMock()
    mock_doc.title = "Test Doc"
    mock_doc.document_type = "TIMETABLE"
    mock_discovery.discover_documents.return_value = [mock_doc]

    mock_download.return_value = "/tmp/fail.pdf"

    # Simulate a crash during hashing/parsing
    with patch("scripts.run_academic_data_sync.calculate_sha256", side_effect=Exception("Fake crash")):
        mock_exists.return_value = True
        run_dry_run()

    mock_session_local.assert_not_called()
    mock_remove.assert_called_with("/tmp/fail.pdf")
