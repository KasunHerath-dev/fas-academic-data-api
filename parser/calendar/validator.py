from typing import List
from datetime import datetime
from parser.calendar.api import ParsedAcademicCalendar, ParsedCalendarPeriod
from parser.src.validator import ValidationStatus, DocumentGateStatus, SessionValidationResult, DocumentValidationResult

class CalendarValidator:
    def __init__(self):
        pass
        
    def _parse_date(self, d_str: str):
        if not d_str:
            return None
        try:
            return datetime.strptime(d_str, "%d-%m-%Y")
        except ValueError:
            return None

    def validate_period(self, period: ParsedCalendarPeriod) -> SessionValidationResult:
        warnings = []
        errors = []
        
        # 1. Period Name Validation
        if not period.period_name:
            errors.append("Empty period name")
            
        # 2. Date Validation
        start_date = self._parse_date(period.start_date)
        end_date = self._parse_date(period.end_date)
        
        if period.start_date and not start_date:
            errors.append(f"Malformed start date: '{period.start_date}'")
        if period.end_date and not end_date:
            errors.append(f"Malformed end date: '{period.end_date}'")
            
        if start_date and end_date:
            if start_date > end_date:
                errors.append(f"Invalid date range: {period.start_date} to {period.end_date}")
                
        if not start_date or not end_date:
            warnings.append("Missing start or end date")
            
        # 3. Duration Validation
        if not period.duration_text:
            warnings.append("Missing duration text")
            
        # 4. OCR confidence
        if period.verification_status == "uncertain":
            warnings.append("OCR uncertainty flagged by extractor")
            
        if period.warnings:
            warnings.extend(period.warnings)
            
        status = ValidationStatus.VALID
        if errors:
            status = ValidationStatus.INVALID
        elif warnings:
            status = ValidationStatus.UNCERTAIN
            
        return SessionValidationResult(
            status=status,
            warnings=warnings,
            errors=errors
        )
        
    def validate_calendar(self, calendar: ParsedAcademicCalendar) -> DocumentValidationResult:
        session_results = []
        doc_warnings = []
        doc_errors = []
        
        valid_count = 0
        uncertain_count = 0
        invalid_count = 0
        
        if not calendar.periods:
            doc_errors.append("No periods found in calendar")
            
        if not calendar.academic_year:
            doc_warnings.append("Missing academic year in calendar header")
            
        for p in calendar.periods:
            res = self.validate_period(p)
            session_results.append(res)
            
            if res.status == ValidationStatus.VALID:
                valid_count += 1
            elif res.status == ValidationStatus.UNCERTAIN:
                uncertain_count += 1
            else:
                invalid_count += 1
                
        # Gate Decision
        gate_status = DocumentGateStatus.SAFE
        
        if invalid_count > 0 or doc_errors:
            gate_status = DocumentGateStatus.REJECT
        elif uncertain_count > 0 or doc_warnings:
            gate_status = DocumentGateStatus.REVIEW_REQUIRED
            
        if len(calendar.periods) > 0 and invalid_count / len(calendar.periods) > 0.5:
            gate_status = DocumentGateStatus.REJECT
            doc_errors.append("Severe parser corruption detected (>50% invalid periods)")
            
        return DocumentValidationResult(
            status=gate_status,
            total_sessions=len(calendar.periods),
            valid_sessions=valid_count,
            uncertain_sessions=uncertain_count,
            invalid_sessions=invalid_count,
            warnings=doc_warnings,
            errors=doc_errors,
            session_results=session_results
        )
