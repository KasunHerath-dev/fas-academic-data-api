import os
import json
import hashlib
from pdf_loader import PDFLoader
from text_extractor import TextExtractor
from table_detector import TableDetector
from cell_parser import CellParser
from session_parser import SessionParser
from session_merger import SessionMerger

def inspect_pdf(filepath, output_dir):
    loader = PDFLoader(filepath)
    try:
        loader.load()
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

    extractor = TextExtractor(loader)
    detector = TableDetector(loader, extractor)
    cell_parser = CellParser()
    session_parser = SessionParser()
    session_merger = SessionMerger()
    
    filename = os.path.basename(filepath)
    pdf_out_dir = os.path.join(output_dir, filename.replace('.pdf', ''))
    os.makedirs(pdf_out_dir, exist_ok=True)
    
    page_count = loader.get_page_count()
    
    all_sessions = []
    
    for i in range(page_count):
        print(f"Inspecting {filename} - Page {i+1}")
        words = extractor.get_words(i)
        words_dict = [{"x0": w[0], "y0": w[1], "x1": w[2], "y1": w[3], "word": w[4].strip(), "block_no": w[5], "line_no": w[6], "word_no": w[7]} for w in words]
        
        if detector.is_grid_page(words_dict):
            print(f"Page {i+1} classified as Grid Page. Running Phase 3, 4.1 & 5.")
            dims = extractor.get_page_dimensions(i)
            drawings = extractor.get_drawings(i)
            
            grid_data = detector.detect_grid(words_dict, dims, drawings)
            if not grid_data: continue
            
            # Phase 3
            cell_parser.assign_words(words_dict, grid_data)
            parsed_cells = cell_parser.parse_cells(grid_data)
            
            # Phase 4.1
            sessions, _ = session_parser.parse_sessions(parsed_cells)
            all_sessions.extend(sessions)

    # Phase 5 Merging
    final_sessions, diagnostics = session_merger.merge_sessions(all_sessions)
    
    # Reports
    report = session_merger.generate_report(len(all_sessions), final_sessions, diagnostics)
    
    with open(os.path.join(pdf_out_dir, "phase5_sessions.json"), "w") as f:
        json.dump(final_sessions, f, indent=2)
        
    with open(os.path.join(pdf_out_dir, "phase5_report.json"), "w") as f:
        json.dump(report, f, indent=2)
        
    with open(os.path.join(pdf_out_dir, "phase5_merge_diagnostics.json"), "w") as f:
        json.dump(diagnostics, f, indent=2)
        
    loader.close()
    return report

def main():
    input_dir = "parser/input"
    output_dir = "parser/output/debug"
    os.makedirs(output_dir, exist_ok=True)
    pdfs = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
    for pdf in pdfs:
        inspect_pdf(os.path.join(input_dir, pdf), output_dir)

if __name__ == '__main__':
    main()
