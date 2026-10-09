import os
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

from parser.src.pdf_loader import PDFLoader
from parser.src.text_extractor import TextExtractor
from parser.src.table_detector import TableDetector
from parser.src.cell_parser import CellParser
from parser.src.session_parser import SessionParser
from parser.src.session_merger import SessionMerger

class ParsedSession(BaseModel):
    day: str
    start_time: str
    end_time: str
    module_code: Optional[str]
    module_name: Optional[str] = None
    session_type: Optional[str] = None
    room: Optional[str] = None
    group: Optional[str] = None
    major: Optional[str] = None
    programme: Optional[str] = None
    raw_evidence: Dict[str, Any]
    time_source: str
    verification_status: str
    warnings: List[str]

class ParsedTimetable(BaseModel):
    sessions: List[ParsedSession]
    diagnostics: List[Dict[str, Any]]
    report: Dict[str, Any]

def parse_timetable(pdf_path: str) -> ParsedTimetable:
    """
    Public entry point for the production PDF parser.
    Takes a path to a temporary PDF file and returns a structured ParsedTimetable.
    Raises ValueError if parsing fails due to malformed PDF or unsupported layout.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at {pdf_path}")
        
    loader = PDFLoader(pdf_path)
    try:
        loader.load()
    except Exception as e:
        raise ValueError(f"Failed to load PDF: {e}")

    try:
        extractor = TextExtractor(loader)
        detector = TableDetector(loader, extractor)
        cell_parser = CellParser()
        session_parser = SessionParser()
        session_merger = SessionMerger()
        
        page_count = loader.get_page_count()
        all_sessions = []
        
        grid_found = False
        
        for i in range(page_count):
            words = extractor.get_words(i)
            words_dict = [{"x0": w[0], "y0": w[1], "x1": w[2], "y1": w[3], "word": w[4].strip(), "block_no": w[5], "line_no": w[6], "word_no": w[7]} for w in words]
            
            if detector.is_grid_page(words_dict):
                grid_found = True
                dims = extractor.get_page_dimensions(i)
                drawings = extractor.get_drawings(i)
                
                grid_data = detector.detect_grid(words_dict, dims, drawings)
                if not grid_data: 
                    continue
                
                cell_parser.assign_words(words_dict, grid_data)
                parsed_cells = cell_parser.parse_cells(grid_data)
                
                sessions, _ = session_parser.parse_sessions(parsed_cells)
                all_sessions.extend(sessions)

        if not grid_found:
            raise ValueError("No timetable grid found in PDF (Unsupported layout or empty timetable)")

        final_sessions, diagnostics = session_merger.merge_sessions(all_sessions)
        report = session_merger.generate_report(len(all_sessions), final_sessions, diagnostics)
        
        parsed_session_objects = []
        for s in final_sessions:
            # Map raw parser fields to structured output fields
            # Verification status logic based on warnings/ambiguities
            status = "uncertain" if s.get("warnings") or not s.get("validation", {}).get("moduleCode", True) else "verified"
            
            parsed_session_objects.append(ParsedSession(
                day=s["day"],
                start_time=s["startTime"],
                end_time=s["endTime"],
                module_code=s.get("moduleCode") or s.get("rawModuleCode"),
                session_type=s.get("classType"),
                room=s.get("room"),
                group=s.get("group"),
                raw_evidence=s.get("rawEvidence", {}),
                time_source=s.get("timeSource", "inferred"),
                verification_status=status,
                warnings=s.get("warnings", [])
            ))
            
        return ParsedTimetable(
            sessions=parsed_session_objects,
            diagnostics=diagnostics,
            report=report
        )
    finally:
        loader.close()
