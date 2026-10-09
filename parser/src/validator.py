import re
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel

from parser.src.api import ParsedTimetable, ParsedSession

class ValidationStatus(Enum):
    VALID = "VALID"
    UNCERTAIN = "UNCERTAIN"
    INVALID = "INVALID"

class DocumentGateStatus(Enum):
    SAFE = "SAFE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECT = "REJECT"

class SessionValidationResult(BaseModel):
    status: ValidationStatus
    warnings: List[str]
    errors: List[str]

class DocumentValidationResult(BaseModel):
    status: DocumentGateStatus
    total_sessions: int
    valid_sessions: int
    uncertain_sessions: int
    invalid_sessions: int
    warnings: List[str]
    errors: List[str]
    session_results: List[SessionValidationResult]

class TimetableValidator:
    VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
    
    def __init__(self):
        pass
        
    def _parse_time(self, t_str: str):
        try:
            h, m = map(int, t_str.split(':'))
            return h * 60 + m
        except (ValueError, AttributeError):
            return None

    def validate_session(self, session: ParsedSession) -> SessionValidationResult:
        warnings = []
        errors = []
        
        # 1. Day Validation
        if not session.day or session.day not in self.VALID_DAYS:
            errors.append(f"Invalid or unknown day: '{session.day}'")
            
        # 2. Time Validation
        start_min = self._parse_time(session.start_time)
        end_min = self._parse_time(session.end_time)
        
        if start_min is None:
            errors.append(f"Malformed start time: '{session.start_time}'")
        if end_min is None:
            errors.append(f"Malformed end time: '{session.end_time}'")
            
        if start_min is not None and end_min is not None:
            if start_min > end_min:
                errors.append(f"Invalid time range: {session.start_time} to {session.end_time}")
            elif (end_min - start_min) == 0:
                errors.append("Zero duration session")
                
        # 3. Lunch Validation
        code_lower = (session.module_code or "").lower().replace(" ", "")
        if "lunch" in code_lower:
            errors.append("Lunch row incorrectly parsed as a session")
            
        # 4. Module Code Validation
        if not session.module_code:
            errors.append("Empty module code")
        else:
            # Check for suspicious OCR (e.g. ELTN 3+53 instead of 3153)
            # A typical FAS module code is like 'ELTN 2112' or 'MATH 1122'
            if "+" in session.module_code or "=" in session.module_code or re.search(r'[^\w\s-]', session.module_code):
                warnings.append(f"Suspicious module code OCR: '{session.module_code}'")
                
        # 5. Room Normalization/Validation
        # We allow missing rooms, but if present, we could do basic sanity checks.
        # Normalization is mostly done upstream or here.
        if session.room:
            # Check if it looks like a crazy string (OCR failure)
            if len(session.room) > 50:
                warnings.append("Unusually long room name")
                
        # 6. Group Validation
        if session.group:
            # Ambiguous group like "Gp. l" vs "Gp. I"
            if re.search(r'\bl\b|\bll\b|\blll\b|\blV\b', session.group):
                warnings.append(f"Ambiguous lowercase 'L' in group OCR: '{session.group}'")
                
        # Existing warnings from parser (e.g., ambiguous merges)
        if session.warnings:
            warnings.extend(session.warnings)
            
        # Determine Status
        status = ValidationStatus.VALID
        if errors:
            status = ValidationStatus.INVALID
        elif warnings or session.verification_status == "uncertain":
            status = ValidationStatus.UNCERTAIN
            
        return SessionValidationResult(
            status=status,
            warnings=warnings,
            errors=errors
        )
        
    def validate_timetable(self, timetable: ParsedTimetable) -> DocumentValidationResult:
        session_results = []
        doc_warnings = []
        doc_errors = []
        
        valid_count = 0
        uncertain_count = 0
        invalid_count = 0
        
        if not timetable.sessions:
            doc_errors.append("No sessions found in timetable")
            
        for s in timetable.sessions:
            res = self.validate_session(s)
            session_results.append(res)
            
            if res.status == ValidationStatus.VALID:
                valid_count += 1
            elif res.status == ValidationStatus.UNCERTAIN:
                uncertain_count += 1
            else:
                invalid_count += 1
                
        # Check Overlaps & Duplicates
        valid_sessions_only = [
            (i, s) for i, (s, r) in enumerate(zip(timetable.sessions, session_results)) 
            if r.status != ValidationStatus.INVALID
        ]
        
        for i, s1 in valid_sessions_only:
            for j, s2 in valid_sessions_only:
                if i >= j:
                    continue
                if s1.day != s2.day:
                    continue
                    
                # Time overlap check
                start1 = self._parse_time(s1.start_time)
                end1 = self._parse_time(s1.end_time)
                start2 = self._parse_time(s2.start_time)
                end2 = self._parse_time(s2.end_time)
                
                if start1 is None or end1 is None or start2 is None or end2 is None:
                    continue
                    
                # Overlap logic: max(start) < min(end)
                if max(start1, start2) < min(end1, end2):
                    # It's an overlap
                    if s1.module_code == s2.module_code and s1.room == s2.room and s1.group == s2.group and s1.start_time == s2.start_time and s1.end_time == s2.end_time:
                        doc_warnings.append(f"Likely duplicate session detected: {s1.module_code} on {s1.day} {s1.start_time}-{s1.end_time}")
                    else:
                        # Just an overlap warning
                        # Might be normal if different groups/rooms, so just a warning
                        # For same room, it's definitely suspicious
                        if s1.room and s2.room and s1.room == s2.room:
                            doc_warnings.append(f"Room overlap detected in {s1.room} on {s1.day} between {s1.module_code} and {s2.module_code}")
                        
        # Gate Decision
        gate_status = DocumentGateStatus.SAFE
        
        if invalid_count > 0 or doc_errors:
            gate_status = DocumentGateStatus.REJECT
        elif uncertain_count > 0 or doc_warnings:
            gate_status = DocumentGateStatus.REVIEW_REQUIRED
            
        # Exception: severe corruption
        if len(timetable.sessions) > 0 and invalid_count / len(timetable.sessions) > 0.5:
            # Over half are invalid, extreme corruption
            gate_status = DocumentGateStatus.REJECT
            doc_errors.append("Severe parser corruption detected (>50% invalid sessions)")
            
        return DocumentValidationResult(
            status=gate_status,
            total_sessions=len(timetable.sessions),
            valid_sessions=valid_count,
            uncertain_sessions=uncertain_count,
            invalid_sessions=invalid_count,
            warnings=doc_warnings,
            errors=doc_errors,
            session_results=session_results
        )
