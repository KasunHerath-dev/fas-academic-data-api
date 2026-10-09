import json
import cv2

class CellParser:
    def __init__(self):
        pass

    def assign_words(self, words, grid_data):
        assigned = []
        ambiguous = []
        cells = grid_data["cells"]
        
        # Build cell lookup by day and row
        cell_lookup = {}
        for c in cells:
            c["words"] = []
            c["ambiguous"] = False
            cell_lookup[(c["day"], c["startTime"])] = c
            
        for w in words:
            # Skip header stuff (Y < grid start)
            if not grid_data["rows"]: continue
            if w["y1"] < grid_data["rows"][0]["y0"] - 10:
                continue
                
            center_x = (w["x0"] + w["x1"]) / 2
            center_y = (w["y0"] + w["y1"]) / 2
            
            # Find row
            matched_row = None
            for r in grid_data["rows"]:
                if r["y0"] <= center_y <= r["y1"]:
                    matched_row = r
                    break
            
            if not matched_row:
                # Could be slightly outside, find closest
                matched_row = min(grid_data["rows"], key=lambda r: min(abs(r["y0"] - center_y), abs(r["y1"] - center_y)))
                if min(abs(matched_row["y0"] - center_y), abs(matched_row["y1"] - center_y)) > 20:
                    continue # Too far
                    
            # Find column
            matched_col = None
            min_dist = float('inf')
            is_ambiguous = False
            
            for col in grid_data["columns"]:
                col_center = (col["x0"] + col["x1"]) / 2
                dist = abs(center_x - col_center)
                if col["x0"] <= center_x <= col["x1"]:
                    matched_col = col
                    is_ambiguous = False
                    break
                elif dist < min_dist:
                    min_dist = dist
                    matched_col = col
                    is_ambiguous = True
                    
            if matched_col and matched_col["name"] != "Time":
                c = cell_lookup[(matched_col["name"], matched_row["startTime"])]
                c["words"].append(w)
                if is_ambiguous:
                    ambiguous.append({"word": w, "assigned_cell": (matched_col["name"], matched_row["startTime"])})
                    c["ambiguous"] = True
                    
        return ambiguous

    def group_lines(self, words):
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
            
        result = []
        for line in lines:
            line_text = " ".join([w["word"] for w in line])
            result.append({
                "y": line[0]["y0"],
                "text": line_text,
                "words": line
            })
        return result

    def cluster_sessions(self, lines):
        # A simple spatial clustering: group by vertical gaps or significant horizontal gaps
        # For now, treat it as one cluster unless there's a big vertical gap
        if not lines:
            return []
            
        clusters = []
        current_cluster = [lines[0]]
        
        for i in range(1, len(lines)):
            prev_line = lines[i-1]
            curr_line = lines[i]
            
            y_gap = curr_line["y"] - prev_line["y"]
            
            # If Y gap is significantly large (>15 points), split cluster
            if y_gap > 15:
                clusters.append(current_cluster)
                current_cluster = [curr_line]
            else:
                # Check horizontal splitting within a line if multiple sessions side-by-side
                # We will handle side-by-side by looking for big X gaps in words, but for now
                # keep vertical clustering as priority.
                current_cluster.append(curr_line)
                
        if current_cluster:
            clusters.append(current_cluster)
            
        # Format clusters
        formatted = []
        for cl in clusters:
            formatted.append({
                "lines": cl,
                "needsSemanticReview": len(clusters) > 1
            })
        return formatted

    def parse_cells(self, grid_data):
        parsed_cells = []
        for c in grid_data["cells"]:
            lines = self.group_lines(c["words"])
            clusters = self.cluster_sessions(lines)
            
            raw_text = [l["text"] for l in lines]
            
            parsed_cells.append({
                "day": c["day"],
                "startTime": c["startTime"],
                "endTime": c["endTime"],
                "isLunch": c.get("isLunch", False),
                "timeSource": c.get("timeSource"),
                "timeInferenceReason": c.get("timeInferenceReason"),
                "rawText": raw_text,
                "words": c["words"],
                "lines": lines,
                "clusters": clusters,
                "ambiguous": c.get("ambiguous", False)
            })
        return parsed_cells
