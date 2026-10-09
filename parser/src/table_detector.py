import re
import cv2
import json
from datetime import datetime, timedelta

class TableDetector:
    def __init__(self, loader, extractor):
        self.loader = loader
        self.extractor = extractor
        self.days_expected = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.time_pattern = re.compile(r'(\d{2}[:\.]\d{2})\s*(a\.m\.|p\.m\.|AM|PM)?\s*[-–]\s*(\d{2}[:\.]\d{2})\s*(a\.m\.|p\.m\.|AM|PM)?', re.IGNORECASE)

    def is_grid_page(self, words):
        text_content = " ".join([w["word"] for w in words])
        found = sum(1 for d in self.days_expected if d in text_content)
        return found >= 3

    def detect_grid(self, words, page_dim, drawings=None):
        headers = {}
        time_header = None
        for w in words:
            word_clean = w["word"].strip()
            if word_clean in self.days_expected:
                headers[word_clean] = w
            elif word_clean == "Time":
                time_header = w

        if not time_header or not headers:
            return None

        sorted_days = sorted(headers.values(), key=lambda x: (x["x0"] + x["x1"])/2)
        columns = []
        all_headers = [time_header] + sorted_days
        for i in range(len(all_headers)):
            header = all_headers[i]
            name = header["word"].strip()
            
            if i == 0:
                x0 = header["x0"] - 20
            else:
                prev = all_headers[i-1]
                prev_c = (prev["x0"] + prev["x1"])/2
                curr_c = (header["x0"] + header["x1"])/2
                x0 = (prev_c + curr_c) / 2
                
            if i == len(all_headers) - 1:
                x1 = page_dim["width"] - 20
            else:
                next_h = all_headers[i+1]
                curr_c = (header["x0"] + header["x1"])/2
                next_c = (next_h["x0"] + next_h["x1"])/2
                x1 = (curr_c + next_c) / 2
                
            columns.append({"name": name, "x0": x0, "x1": x1, "center_x": (header["x0"] + header["x1"])/2})
            
        time_col = columns[0]
        day_columns = columns[1:]

        words.sort(key=lambda w: (w["y0"], w["x0"]))
        lines = []
        current_y = None
        current_line = []
        for w in words:
            if current_y is None:
                current_y = w["y0"]
            if abs(w["y0"] - current_y) < 4:
                current_line.append(w)
            else:
                lines.append(current_line)
                current_line = [w]
                current_y = w["y0"]
        if current_line:
            lines.append(current_line)

        explicit_time_labels = []
        lunch_rect = None
        
        for line in lines:
            sorted_line = sorted(line, key=lambda w: w["x0"])
            line_text = " ".join([w["word"] for w in sorted_line])
            if "L U N C H" in line_text or "LUNCH" in line_text:
                lunch_rect = {"text": "LUNCH", "y0": min(w["y0"] for w in line), "y1": max(w["y1"] for w in line)}
                continue
                
            if sorted_line[0]["x0"] < time_col["x1"]:
                match = self.time_pattern.search(line_text)
                if match:
                    start_t = match.group(1).replace('.', ':')
                    end_t = match.group(3).replace('.', ':')
                    explicit_time_labels.append({
                        "startTime": start_t,
                        "endTime": end_t,
                        "y_center": (line[0]["y0"] + max(w["y1"] for w in line))/2
                    })

        # Process drawings for geometric Y boundaries
        y_lines = []
        if drawings:
            for d in drawings:
                rect = d.get('rect')
                if rect and rect[3] - rect[1] < 5: # Horizontal-ish
                    if rect[2] - rect[0] > 50: # reasonably wide
                        y_lines.append(rect[1])
        
        y_lines.sort()
        geometric_y = []
        curr_y = None
        for y in y_lines:
            if curr_y is None:
                curr_y = y
                geometric_y.append(y)
            elif abs(y - curr_y) > 3:
                curr_y = y
                geometric_y.append(y)

        # Filter out lines that are above the headers
        header_bottom = time_header["y1"] + 10
        geometric_y = [y for y in geometric_y if y > header_bottom]
        
        rows = []
        for i in range(len(geometric_y) - 1):
            y0 = geometric_y[i]
            y1 = geometric_y[i+1]
            if y1 - y0 < 20:
                continue
            
            row = {
                "y0": y0,
                "y1": y1,
                "startTime": None,
                "endTime": None,
                "isLunch": False,
                "timeSource": None,
                "timeInferenceReason": None
            }
            
            # Check for Lunch
            if lunch_rect and y0 <= (lunch_rect["y0"] + lunch_rect["y1"])/2 <= y1:
                row["isLunch"] = True
                rows.append(row)
                continue
                
            # Check for explicit label
            matched_label = None
            for label in explicit_time_labels:
                if y0 <= label["y_center"] <= y1:
                    matched_label = label
                    break
                    
            if matched_label:
                row["startTime"] = matched_label["startTime"]
                row["endTime"] = matched_label["endTime"]
                row["timeSource"] = "explicit"
            else:
                row["timeSource"] = "missing"
                
            rows.append(row)
            
        # Inference pass
        for i in range(len(rows)):
            if rows[i]["timeSource"] == "missing" and not rows[i]["isLunch"]:
                # Try to infer from above
                if i > 0 and rows[i-1]["endTime"]:
                    # Assume adjacent
                    prev_end = rows[i-1]["endTime"]
                    # Calculate + 1 hour (assuming standard)
                    try:
                        t = datetime.strptime(prev_end, "%H:%M")
                        t_next = t + timedelta(hours=1)
                        rows[i]["startTime"] = prev_end
                        rows[i]["endTime"] = t_next.strftime("%H:%M")
                        rows[i]["timeSource"] = "inferred"
                        rows[i]["timeInferenceReason"] = "missing PDF time label; derived from adjacent timetable row structure"
                    except:
                        pass
                        
        # Filter out rows that are entirely missing (no explicit, no inferred, not lunch)
        valid_rows = [r for r in rows if r["timeSource"] in ("explicit", "inferred") or r["isLunch"]]

        cells = []
        for row in valid_rows:
            for col in day_columns:
                cells.append({
                    "day": col["name"],
                    "startTime": row.get("startTime"),
                    "endTime": row.get("endTime"),
                    "isLunch": row["isLunch"],
                    "timeSource": row.get("timeSource"),
                    "timeInferenceReason": row.get("timeInferenceReason"),
                    "bounds": {
                        "x0": col["x0"],
                        "y0": row["y0"],
                        "x1": col["x1"],
                        "y1": row["y1"]
                    }
                })

        return {
            "columns": columns,
            "rows": valid_rows,
            "lunch_row": lunch_rect,
            "cells": cells
        }

    def draw_debug(self, img_path, out_path, parsed_cells, grid_data):
        img = cv2.imread(img_path)
        if img is None:
            return
            
        for col in grid_data["columns"]:
            cv2.line(img, (int(col["x0"]*2), 0), (int(col["x0"]*2), img.shape[0]), (255, 0, 0), 2)
            cv2.line(img, (int(col["x1"]*2), 0), (int(col["x1"]*2), img.shape[0]), (255, 0, 0), 2)
            
        for row in grid_data["rows"]:
            cv2.line(img, (0, int(row["y0"]*2)), (img.shape[1], int(row["y0"]*2)), (0, 0, 255), 2)
            cv2.line(img, (0, int(row["y1"]*2)), (img.shape[1], int(row["y1"]*2)), (0, 0, 255), 2)
            
        if grid_data["lunch_row"]:
            lr = grid_data["lunch_row"]
            cv2.rectangle(img, (0, int(lr["y0"]*2)), (img.shape[1], int(lr["y1"]*2)), (0, 255, 0), 2)
            
        for c, p_cell in zip(grid_data["cells"], parsed_cells):
            b = c["bounds"]
            wc = len(p_cell["words"])
            cv2.rectangle(img, (int(b["x0"]*2), int(b["y0"]*2)), (int(b["x1"]*2), int(b["y1"]*2)), (255, 255, 0), 1)
            cv2.putText(img, f"{c['day']} {c['startTime']} ({wc}w)", (int(b["x0"]*2)+5, int(b["y0"]*2)+15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1)
            
        cv2.imwrite(out_path, img)

