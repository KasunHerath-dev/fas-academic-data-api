import json
import os
import sys

def make_id(s):
    mod = s.get('moduleCode') or s.get('rawModuleCode') or 'Unknown'
    ct = s.get('classType') or 'Unknown'
    y = s.get('rawEvidence', {}).get('module', {}).get('y', '0')
    return f"{s['day']}_{s['startTime']}_{s['endTime']}_{mod}_{ct}_{y}"

def review_golden(level="Level-23"):
    expected_path = f"parser/tests/golden/{level}/expected_sessions.json"
    actual_path = f"parser/output/debug/{level}/phase5_sessions.json"
    
    if not os.path.exists(expected_path) or not os.path.exists(actual_path):
        print(f"Missing files for {level}")
        return
        
    with open(expected_path) as f:
        expected_data = json.load(f)
    with open(actual_path) as f:
        actual = json.load(f)
        
    expected_sessions = expected_data.get("sessions", []) if isinstance(expected_data, dict) else expected_data
    
    exp_dict = {make_id(s): s for s in expected_sessions}
    act_dict = {make_id(s): s for s in actual}
    
    verified_exp = {k: v for k, v in exp_dict.items() if v.get("verificationStatus") == "verified"}
    uncertain_exp = {k: v for k, v in exp_dict.items() if v.get("verificationStatus") == "uncertain"}
    
    report = {
        "expected_count": len(expected_sessions),
        "verified_expected_count": len(verified_exp),
        "uncertain_expected_count": len(uncertain_exp),
        "extracted_count": len(actual),
        "exact_match_count": 0,
        "missing_count": 0,
        "unexpected_count": 0,
        "field_mismatch_count": 0,
    }
    
    html = f"<html><head><title>Golden Review {level}</title></head><body>"
    html += f"<h1>Golden Review {level}</h1>"
    
    if len(uncertain_exp) > 0:
        html += "<p><b>Metrics are partial because some source records remain uncertain.</b></p>"
        
    html += f"<p>Expected (Verified): {report['verified_expected_count']} | Expected (Uncertain): {report['uncertain_expected_count']} | Extracted: {report['extracted_count']}</p>"
    
    for eid, es in verified_exp.items():
        if eid not in act_dict:
            report["missing_count"] += 1
            html += f"<div style='color:red;'><b>MISSING:</b> {eid}</div>"
            continue
            
        acts = act_dict[eid]
        mismatches = []
        for field in ["moduleCode", "classType", "group", "room"]:
            if str(es.get(field)) != str(acts.get(field)):
                mismatches.append(f"{field}: Expected {es.get(field)}, Got {acts.get(field)}")
                
        if mismatches:
            report["field_mismatch_count"] += 1
            html += f"<div style='color:red;'><b>MISMATCH:</b> {eid} -> {', '.join(mismatches)}</div>"
        else:
            report["exact_match_count"] += 1
            html += f"<div style='color:green;'><b>MATCH:</b> {eid}</div>"
            
    for aid in act_dict:
        if aid not in verified_exp:
            if aid in uncertain_exp:
                html += f"<div style='color:orange;'><b>MATCHED UNCERTAIN:</b> {aid}</div>"
            else:
                report["unexpected_count"] += 1
                html += f"<div style='color:purple;'><b>UNEXPECTED:</b> {aid}</div>"
            
    if report["verified_expected_count"] > 0:
        report["precision"] = report["exact_match_count"] / (report["exact_match_count"] + report["field_mismatch_count"] + report["unexpected_count"]) if (report["exact_match_count"] + report["field_mismatch_count"] + report["unexpected_count"]) else 0
        report["recall"] = report["exact_match_count"] / report["verified_expected_count"]
        
    html += "</body></html>"
    
    out_dir = f"parser/output/debug/{level}"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/golden_review.html", "w") as f:
        f.write(html)
        
    with open(f"{out_dir}/golden_review.json", "w") as f:
        json.dump(report, f, indent=2)
        
    return report

if __name__ == "__main__":
    report = review_golden()
    if report:
        print(json.dumps(report, indent=2))

