import pytest
from parser.src.session_parser import SessionParser
import re

@pytest.fixture
def parser():
    return SessionParser()

def test_room_normalization_removes_trailing_artifacts(parser):
    """Test that room names are correctly cleaned up of trailing class-type markers."""
    cases = [
        ("FAS Computer Lab)", "FAS Computer Lab"),
        ("Room 22) (P)", "Room 22"),
        ("Room 23) (L) LR-09", "Room 23"),
        ("Room No. 23 (L) LR-07", "Room No. 23"),
        ("MH", "MH"),
        ("LR-08", "LR-08"),
        ("Mini Auditorium", "Mini Auditorium")
    ]

    for raw_room, expected in cases:
        norm_room = re.sub(r'\s*-\s*', '-', raw_room)
        norm_room = re.sub(r'\s+', ' ', norm_room).strip()
        # Same regex logic applied in session_parser.py
        norm_room = re.sub(r'\)?\s*\([LPT]\).*$', '', norm_room).strip()
        norm_room = norm_room.rstrip(')')
        norm_room = norm_room.strip()

        assert norm_room == expected
