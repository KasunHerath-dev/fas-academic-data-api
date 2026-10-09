import re

class SessionParser:
    def __init__(self):
        self.module_pattern = re.compile(r'([A-Z]{4})\s+(\d{4})')
        self.class_type_pattern = re.compile(r'\(\s*([LPT])\s*\)')
        self.group_pattern = re.compile(r'Gp\.\s*([IVX1-4]+)', re.IGNORECASE)
        self.suspicious_group_pattern = re.compile(r'Gp\.\s*([a-zA-Z1-9]+)', re.IGNORECASE)
        self.suspicious_module_pattern = re.compile(r'([A-Z]{4})\s+([\d\+\-\ᵻ]{4})')
        # Room regex supports slashes for multiple rooms e.g. LR 01/02/03
        self.room_pattern = re.compile(r'(MH|LR\s*-\s*[\d/]+|LR\s*[\d/]+|Mini\s*Auditorium|Room.*|ELTN\s*Lab|FAS.*)', re.IGNORECASE)

    def parse_sessions(self, parsed_cells):
        all_sessions = []
        diagnostics = []
        for cell in parsed_cells:
            if cell["isLunch"] or not cell["words"]:
                continue
            
            words = cell["words"]
            words.sort(key=lambda w: (w["y0"], w["x0"]))
            
            lines = []
            curr_line = []
            curr_y = None
            for w in words:
                if curr_y is None:
                    curr_y = w["y0"]
                if abs(w["y0"] - curr_y) < 5:
                    curr_line.append(w)
                else:
                    lines.append(curr_line)
                    curr_line = [w]
                    curr_y = w["y0"]
            if curr_line:
                lines.append(curr_line)

            anchors = []
            for line_idx, line in enumerate(lines):
                text = " ".join([w["word"] for w in line])
                for match in self.suspicious_module_pattern.finditer(text):
                    start_idx, end_idx = match.span()
                    anchor_words = []
                    char_count = 0
                    for w in line:
                        w_len = len(w["word"])
                        if char_count + w_len >= start_idx and char_count <= end_idx:
                            anchor_words.append(w)
                        char_count += w_len + 1
                    
                    if anchor_words:
                        anchors.append({
                            "text": match.group(0),
                            "words": anchor_words,
                            "x_center": sum(w["x0"] + w["x1"] for w in anchor_words) / (2 * len(anchor_words)),
                            "y_center": sum(w["y0"] + w["y1"] for w in anchor_words) / (2 * len(anchor_words))
                        })

            if not anchors:
                continue

            session_groups = {i: {"anchor": a, "other_words": []} for i, a in enumerate(anchors)}
            
            for line in lines:
                for w in line:
                    is_anchor = any(w in a["words"] for a in anchors)
                    if is_anchor: continue
                    
                    w_cx = (w["x0"] + w["x1"]) / 2
                    w_cy = (w["y0"] + w["y1"]) / 2
                    
                    best_anchor_idx = -1
                    min_score = float('inf')
                    for i, a in enumerate(anchors):
                        if w_cy < a["y_center"] - 10: 
                            continue
                        dx = abs(w_cx - a["x_center"])
                        dy = w_cy - a["y_center"]
                        score = dx * 1.5 + dy
                        if score < min_score and dx < 80: # Give more horizontal leeway but keep it aligned
                            min_score = score
                            best_anchor_idx = i
                            
                    if best_anchor_idx != -1:
                        session_groups[best_anchor_idx]["other_words"].append(w)

            for idx, grp in session_groups.items():
                anchor = grp["anchor"]
                other_words = grp["other_words"]
                all_text = " ".join([w["word"] for w in anchor["words"]] + [w["word"] for w in other_words])
                
                session = {
                    "day": cell["day"],
                    "startTime": cell["startTime"],
                    "endTime": cell["endTime"],
                    "timeSource": cell.get("timeSource"),
                    "timeInferenceReason": cell.get("timeInferenceReason"),
                    "moduleCode": None,
                    "rawModuleCode": anchor["text"],
                    "classType": None,
                    "rawClassType": None,
                    "group": None,
                    "rawGroup": None,
                    "room": None,
                    "rawRoom": None,
                    "warnings": [],
                    "rawEvidence": {
                        "module": {"text": anchor["text"], "x": anchor["x_center"], "y": anchor["y_center"]}
                    },
                    "validation": {},
                    "confidence": 0
                }
                
                diag = {
                    "cell": f"{cell['day']} {cell['startTime']}-{cell['endTime']}",
                    "rawCellText": cell["rawText"],
                    "moduleCode": anchor["text"],
                    "nearbyGroupCandidates": [],
                    "selectedGroup": None,
                    "groupReason": "None",
                    "nearbyRoomCandidates": [],
                    "selectedRoom": None,
                    "roomReason": "None",
                    "associationEvidence": {}
                }
                
                if self.module_pattern.fullmatch(anchor["text"]):
                    session["moduleCode"] = anchor["text"]
                    session["validation"]["moduleCode"] = True
                    session["confidence"] += 40
                else:
                    session["warnings"].append(f"Suspicious module code: {anchor['text']}")
                    session["validation"]["moduleCode"] = False
                    session["confidence"] -= 20
                    
                other_text = " ".join([w["word"] for w in other_words])
                
                ct_match = self.class_type_pattern.search(anchor["text"] + " " + other_text)
                if ct_match:
                    session["rawClassType"] = ct_match.group(0)
                    session["classType"] = ct_match.group(1)
                    session["validation"]["classType"] = True
                    session["confidence"] += 20
                else:
                    session["validation"]["classType"] = False
                    
                grp_match = self.suspicious_group_pattern.search(other_text)
                if grp_match:
                    raw_grp = grp_match.group(0)
                    session["rawGroup"] = raw_grp
                    clean_grp = grp_match.group(1).upper()
                    diag["nearbyGroupCandidates"].append(raw_grp)
                    
                    if self.group_pattern.fullmatch(raw_grp):
                        session["group"] = clean_grp
                        session["validation"]["group"] = True
                        session["confidence"] += 15
                        diag["selectedGroup"] = raw_grp
                        diag["groupReason"] = "Strong spatial proximity and regex match"
                    else:
                        session["warnings"].append(f"Possible OCR ambiguity in group: {raw_grp}")
                        session["validation"]["group"] = False
                        session["confidence"] -= 10
                        diag["groupReason"] = "Suspicious OCR pattern"
                else:
                    if session["classType"] == "P":
                        diag["groupReason"] = "No nearby group pattern detected in spatial cluster"
                        
                room_match = self.room_pattern.search(other_text)
                if room_match:
                    raw_room = room_match.group(0)
                    session["rawRoom"] = raw_room
                    norm_room = re.sub(r'\s*-\s*', '-', raw_room)
                    norm_room = re.sub(r'\s+', ' ', norm_room).strip()
                    session["room"] = norm_room
                    session["validation"]["room"] = True
                    session["confidence"] += 25
                    diag["nearbyRoomCandidates"].append(raw_room)
                    diag["selectedRoom"] = raw_room
                    diag["roomReason"] = "Strong spatial proximity and regex match"
                else:
                    session["validation"]["room"] = False
                    diag["roomReason"] = "No nearby room pattern detected in spatial cluster"

                all_sessions.append(session)
                diagnostics.append(diag)
                
        return all_sessions, diagnostics

    def generate_report(self, sessions, diagnostics, total_cells):
        report = {
            "totalSessions": len(sessions),
            "completeSessions": 0,
            "missingRoom": 0,
            "missingGroup": 0,
            "suspiciousModule": 0,
            "ambiguousAssociations": 0,
            "multipleSessionCells": 0
        }
        
        cell_counts = {}
        for s in sessions:
            key = (s["day"], s["startTime"])
            cell_counts[key] = cell_counts.get(key, 0) + 1
            
        report["multipleSessionCells"] = sum(1 for v in cell_counts.values() if v > 1)
        
        for s in sessions:
            is_complete = True
            if s["warnings"]:
                is_complete = False
                if any("module code" in w for w in s["warnings"]):
                    report["suspiciousModule"] += 1
                if any("group" in w for w in s["warnings"]):
                    report["ambiguousAssociations"] += 1
            if not s["room"]:
                report["missingRoom"] += 1
                is_complete = False
            if not s["group"] and s["classType"] == "P":
                report["missingGroup"] += 1
                is_complete = False
                
            if is_complete:
                report["completeSessions"] += 1
                
        return report

