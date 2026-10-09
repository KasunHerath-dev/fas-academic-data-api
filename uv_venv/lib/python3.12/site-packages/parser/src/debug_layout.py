import fitz
import sys

def debug_layout(filepath):
    doc = fitz.open(filepath)
    for page_num in range(len(doc)):
        print(f"\\n--- PAGE {page_num + 1} ---")
        page = doc.load_page(page_num)
        
        # Look at drawings (rectangles/paths)
        drawings = page.get_drawings()
        rects = [d for d in drawings if any(item[0] == "re" for item in d["items"])]
        paths = [d for d in drawings if any(item[0] not in ("re", "l") for item in d["items"])]
        print(f"Drawings: {len(drawings)} total, {len(rects)} containing rects, {len(paths)} complex paths")
        
        words = page.get_text("words")
        # Words format: x0, y0, x1, y1, word, block_no, line_no, word_no
        
        # Group into rough Y bands (lines)
        lines = []
        words.sort(key=lambda w: (w[1], w[0]))
        current_y = None
        current_line = []
        for w in words:
            if current_y is None:
                current_y = w[1]
            if abs(w[1] - current_y) < 4:  # 4 pt tolerance
                current_line.append(w)
            else:
                lines.append(current_line)
                current_line = [w]
                current_y = w[1]
        if current_line:
            lines.append(current_line)
            
        print(f"Total lines grouped: {len(lines)}")
        for i, line in enumerate(lines[:30]): # print first 30 lines to see header, times, days
            text = " ".join(w[4] for w in line)
            x_range = f"X: {line[0][0]:.1f} - {line[-1][2]:.1f}"
            y_pos = f"Y: {line[0][1]:.1f}"
            print(f"Line {i}: {y_pos:10} {x_range:20} -> {text}")
            
if __name__ == "__main__":
    debug_layout(sys.argv[1])
