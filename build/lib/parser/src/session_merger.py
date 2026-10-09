import json
from datetime import datetime

class SessionMerger:
    def __init__(self):
        pass

    def _parse_time(self, time_str):
        # Expected format: "08:30"
        return datetime.strptime(time_str, "%H:%M")

    def _calc_duration(self, start_str, end_str):
        start = self._parse_time(start_str)
        end = self._parse_time(end_str)
        diff = (end - start).total_seconds() / 60
        return int(diff)
        
    def _times_adjacent(self, end1, start2):
        return end1 == start2

    def merge_sessions(self, sessions):
        # Sort sessions by day, then startTime, then moduleCode
        # To handle cross-row merging, we group by day and module
        
        days_order = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5}
        sorted_sessions = sorted(sessions, key=lambda s: (days_order.get(s["day"], 99), self._parse_time(s["startTime"]), s["moduleCode"] or s["rawModuleCode"]))
        
        final_sessions = []
        diagnostics = []
        
        merged_indices = set()
        
        for i, s1 in enumerate(sorted_sessions):
            if i in merged_indices:
                continue
                
            current_session = self._clone_session(s1)
            source_cells = [{"day": s1["day"], "startTime": s1["startTime"], "endTime": s1["endTime"], "timeSource": s1.get("timeSource"), "timeInferenceReason": s1.get("timeInferenceReason")}]
            
            # Look ahead for adjacent sessions to merge
            j = i + 1
            while j < len(sorted_sessions):
                if j in merged_indices:
                    j += 1
                    continue
                    
                s2 = sorted_sessions[j]
                
                # Must be same day and module
                if s1["day"] != s2["day"] or (s1["moduleCode"] or s1["rawModuleCode"]) != (s2["moduleCode"] or s2["rawModuleCode"]):
                    j += 1
                    continue
                    
                # Check adjacency
                if not self._times_adjacent(current_session["endTime"], s2["startTime"]):
                    # If they are on the same day/module but not adjacent, we stop merging this chain
                    # (unless it's just out of order, but we sorted by time, so we know it's a gap)
                    # Note: lunch is not adjacent since lunch creates a time gap or if they jump over lunch, end != start
                    break
                    
                # Check merge conditions
                # 1. Class type
                if s1["classType"] != s2["classType"]:
                    diagnostics.append({
                        "mergeDecision": "not_merged",
                        "reason": ["class type mismatch"],
                        "sessions": [s1, s2]
                    })
                    break
                    
                # 2. Group & Room
                # If both have groups and they differ -> NOT MERGED
                # If one has a group and the other doesn't -> AMBIGUOUS
                g1, g2 = s1["group"], s2["group"]
                r1, r2 = s1["room"], s2["room"]
                
                if g1 and g2 and g1 != g2:
                    diagnostics.append({
                        "mergeDecision": "not_merged",
                        "reason": ["group mismatch"],
                        "sessions": [current_session, s2]
                    })
                    break
                    
                if r1 and r2 and r1 != r2:
                    diagnostics.append({
                        "mergeDecision": "not_merged",
                        "reason": ["room mismatch"],
                        "sessions": [current_session, s2]
                    })
                    break
                    
                if (g1 and not g2) or (g2 and not g1):
                    diagnostics.append({
                        "mergeDecision": "ambiguous",
                        "reason": ["group missing in one row"],
                        "sessions": [current_session, s2]
                    })
                    break
                    
                if (r1 and not r2) or (r2 and not r1):
                    diagnostics.append({
                        "mergeDecision": "ambiguous",
                        "reason": ["room missing in one row"],
                        "sessions": [current_session, s2]
                    })
                    break
                    
                # All checks passed! Merge!
                diagnostics.append({
                    "mergeDecision": "merged",
                    "reason": ["same day", "same module", "same class type", "same group", "same room", "adjacent time intervals"],
                    "sessions": [current_session, s2]
                })
                
                # Update current session
                current_session["endTime"] = s2["endTime"]
                source_cells.append({"day": s2["day"], "startTime": s2["startTime"], "endTime": s2["endTime"], "timeSource": s2.get("timeSource"), "timeInferenceReason": s2.get("timeInferenceReason")})
                
                # Combine raw evidence
                if "mergedFrom" not in current_session["rawEvidence"]:
                    current_session["rawEvidence"]["mergedFrom"] = [s1["rawEvidence"]]
                current_session["rawEvidence"]["mergedFrom"].append(s2["rawEvidence"])
                
                merged_indices.add(j)
                j += 1
                
            # Finalize session
            current_session["durationMinutes"] = self._calc_duration(current_session["startTime"], current_session["endTime"])
            current_session["sourceCells"] = source_cells
            final_sessions.append(current_session)

        # Validate final sessions
        for s in final_sessions:
            self._validate_final_session(s)
            
        return final_sessions, diagnostics

    def _clone_session(self, s):
        import copy
        return copy.deepcopy(s)
        
    def _validate_final_session(self, s):
        s["validation"]["duration"] = s["durationMinutes"] > 0
        s["validation"]["timeValid"] = s["startTime"] < s["endTime"]
        
    def generate_report(self, original_count, final_sessions, diagnostics):
        merged = sum(1 for d in diagnostics if d["mergeDecision"] == "merged")
        not_merged = sum(1 for d in diagnostics if d["mergeDecision"] == "not_merged")
        ambiguous = sum(1 for d in diagnostics if d["mergeDecision"] == "ambiguous")
        
        total_duration = sum(s["durationMinutes"] for s in final_sessions)
        
        suspicious = sum(1 for s in final_sessions if s["warnings"])
        missing_room = sum(1 for s in final_sessions if not s["room"])
        missing_group = sum(1 for s in final_sessions if not s["group"] and s["classType"] == "P")
        
        failures = sum(1 for s in final_sessions if not s["validation"].get("duration") or not s["validation"].get("timeValid") or not s["validation"].get("moduleCode"))
        
        return {
            "original_candidate_count": original_count,
            "final_session_count": len(final_sessions),
            "number_merged_actions": merged,
            "number_not_merged_actions": not_merged,
            "number_ambiguous_actions": ambiguous,
            "total_duration_minutes": total_duration,
            "suspicious_sessions": suspicious,
            "missing_rooms": missing_room,
            "missing_groups": missing_group,
            "validation_failures": failures
        }
