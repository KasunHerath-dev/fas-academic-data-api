import os
import re
from typing import List, Dict, Any, Tuple
from pdf2image import convert_from_path
import pytesseract

def extract_calendar_data(pdf_path: str):
    from parser.calendar.api import ParsedAcademicCalendar, ParsedCalendarPeriod
    
    # 1. Convert PDF to Image
    try:
        images = convert_from_path(pdf_path)
    except Exception as e:
        raise ValueError(f"Failed to convert PDF to images: {e}")
        
    if not images:
        raise ValueError("No pages found in PDF")
        
    image = images[0] # Focus on page 1 for now
    
    # 2. Extract OCR Data using pytesseract with bounding boxes
    # PSM 6 assumes a single uniform block of text.
    # Alternatively, we can use image_to_data to get word-level bounding boxes
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    
    # 3. Reconstruct lines and columns based on bounding boxes
    words = []
    n_boxes = len(ocr_data['text'])
    for i in range(n_boxes):
        text = ocr_data['text'][i].strip()
        if text:
            words.append({
                'text': text,
                'left': ocr_data['left'][i],
                'top': ocr_data['top'][i],
                'width': ocr_data['width'][i],
                'height': ocr_data['height'][i],
                'conf': int(ocr_data['conf'][i])
            })
            
    # Group words into lines based on vertical proximity
    lines = []
    current_line = []
    last_top = -100
    
    # Sort by top coordinate first
    words.sort(key=lambda w: w['top'])
    
    for w in words:
        if abs(w['top'] - last_top) > 15 and current_line: # New line threshold
            lines.append(sorted(current_line, key=lambda cw: cw['left']))
            current_line = []
        current_line.append(w)
        last_top = w['top']
        
    if current_line:
        lines.append(sorted(current_line, key=lambda cw: cw['left']))
        
    # Extract Academic Year and Level from top lines
    academic_year = None
    applicable_levels = None
    
    for line in lines[:20]: # Check top lines
        line_text = " ".join(w['text'] for w in line)
        if "ACADEMIC YEAR" in line_text.upper():
            m = re.search(r'20\d{2}/20\d{2}', line_text)
            if m:
                academic_year = m.group(0)
        
        if "LEVEL" in line_text.upper():
            m = re.search(r'LEVEL[\s:]*([0-9\s,]+)', line_text.upper())
            if m:
                applicable_levels = m.group(1).replace(" ", "")
                
    # Parse semesters and periods
    periods = []
    current_semester = None
    
    # Heuristics for columns
    # We expect columns like Period, From, To, Duration
    
    for line in lines:
        line_text = " ".join(w['text'] for w in line)
        line_upper = line_text.upper()
        
        # Semester detection
        if "FIRST SEMESTER" in line_upper:
            current_semester = "FIRST SEMESTER"
            continue
        elif "SECOND SEMESTER" in line_upper:
            current_semester = "SECOND SEMESTER"
            continue
            
        if not current_semester:
            continue
            
        # Ignore header rows
        if "PERIOD" in line_upper and "FROM" in line_upper:
            continue
            
        # Date regex: DD-MM-YYYY or DD.MM.YYYY
        date_pattern = r'\b\d{2}[-.]\d{2}[-.]\d{4}\b'
        dates = list(re.finditer(date_pattern, line_text))
        
        # Duration regex: e.g., "08 Weeks" or "01 Week"
        duration_pattern = r'\b\d{2}\s*Weeks?\b'
        duration_match = re.search(duration_pattern, line_text, re.IGNORECASE)
        
        if len(dates) >= 2 or duration_match:
            # Looks like a period row
            start_date = dates[0].group(0) if len(dates) > 0 else None
            end_date = dates[1].group(0) if len(dates) > 1 else None
            duration = duration_match.group(0) if duration_match else None
            
            # Period name is everything before the first date
            first_date_idx = dates[0].start() if dates else len(line_text)
            if duration_match and duration_match.start() < first_date_idx:
                first_date_idx = duration_match.start()
                
            period_name = line_text[:first_date_idx].strip()
            # Clean up trailing non-alphas
            period_name = re.sub(r'[^a-zA-Z\s]+$', '', period_name).strip()
            
            if not period_name:
                continue
                
            # Confidence check for "UNCERTAIN" status
            # Find the words that contributed to this
            low_conf = False
            for w in line:
                if w['conf'] < 50:
                    low_conf = True
                    
            status = "uncertain" if low_conf else "verified"
            warnings = ["Low OCR confidence"] if low_conf else []
            
            # Check date malformed or ambiguous
            # e.g., year is 2026 or 2027 usually, if it's 2020 might be bad OCR
            if start_date and not re.match(r'\d{2}-\d{2}-20\d{2}', start_date.replace('.', '-')):
                status = "uncertain"
                warnings.append(f"Suspicious start date OCR: {start_date}")
                
            periods.append(ParsedCalendarPeriod(
                semester=current_semester,
                period_name=period_name,
                start_date=start_date.replace('.', '-') if start_date else None,
                end_date=end_date.replace('.', '-') if end_date else None,
                duration_text=duration,
                source_page=1,
                raw_evidence={"raw_line": line_text, "words": [w['text'] for w in line]},
                verification_status=status,
                warnings=warnings
            ))

    return ParsedAcademicCalendar(
        academic_year=academic_year,
        applicable_levels=applicable_levels,
        raw_title=None,
        periods=periods,
        diagnostics=[],
        report={"parsed_periods": len(periods)}
    )
