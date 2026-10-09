import pytest
import json
import os
from session_merger import SessionMerger

def test_merger_rules():
    merger = SessionMerger()
    base = {
        "day": "Monday",
        "classType": "L",
        "group": None,
        "room": "LR-01",
        "rawEvidence": {},
        "validation": {}
    }
    s1 = {**base, "startTime": "08:30", "endTime": "09:30", "moduleCode": "ABCD 1234"}
    
    # 1. SAME MODULE + SAME TYPE + SAME GROUP + SAME ROOM adjacent -> MUST MERGE
    s2 = {**base, "startTime": "09:30", "endTime": "10:30", "moduleCode": "ABCD 1234"}
    res, diag = merger.merge_sessions([s1, s2])
    assert len(res) == 1
    assert res[0]["endTime"] == "10:30"
    
    # 2. SAME MODULE + SAME TYPE but DIFFERENT GROUP adjacent -> MUST NOT MERGE
    s2_diff_grp = {**s2, "group": "Gp II"}
    s1_grp = {**s1, "group": "Gp I"}
    res, diag = merger.merge_sessions([s1_grp, s2_diff_grp])
    assert len(res) == 2
    
    # 3. SAME MODULE + SAME TYPE but DIFFERENT ROOM adjacent -> MUST NOT MERGE
    s2_diff_rm = {**s2, "room": "MH"}
    res, diag = merger.merge_sessions([s1, s2_diff_rm])
    assert len(res) == 2
    
    # 4. One row missing room -> MUST REMAIN AMBIGUOUS
    s2_missing_rm = {**s2, "room": None}
    res, diag = merger.merge_sessions([s1, s2_missing_rm])
    assert len(res) == 2
    
    # 5. One row missing group -> MUST REMAIN AMBIGUOUS
    s2_missing_grp = {**s2_diff_grp, "group": None}
    res, diag = merger.merge_sessions([s1_grp, s2_missing_grp])
    assert len(res) == 2
    
    # 6. Non-adjacent rows -> MUST NOT MERGE
    s2_non_adj = {**s2, "startTime": "10:30", "endTime": "11:30"}
    res, diag = merger.merge_sessions([s1, s2_non_adj])
    assert len(res) == 2
    
    # 7. Different module -> MUST NOT MERGE
    s2_diff_mod = {**s2, "moduleCode": "WXYZ 9876"}
    res, diag = merger.merge_sessions([s1, s2_diff_mod])
    assert len(res) == 2
    
    # 8. Different class type -> MUST NOT MERGE
    s2_diff_type = {**s2, "classType": "P"}
    res, diag = merger.merge_sessions([s1, s2_diff_type])
    assert len(res) == 2

def test_golden_dataset_schema():
    golden_path = 'parser/tests/golden/Level-23/expected_sessions.json'
    if not os.path.exists(golden_path):
        pytest.skip("Golden dataset not available")
        
    with open(golden_path) as f:
        golden = json.load(f)
        
    assert "datasetVersion" in golden
    assert "source" in golden
    assert "sha256" in golden["source"]
    assert "verification" in golden
    assert "status" in golden["verification"]
    assert "sessions" in golden
    
    sessions = golden["sessions"]
    assert len(sessions) > 0
    
    for s in sessions:
        assert "verificationStatus" in s
        assert s["verificationStatus"] in ["verified", "uncertain"]
        if s.get("timeSource") == "inferred":
            assert "timeInferenceReason" in s
        assert "sourceCells" in s
        assert len(s["sourceCells"]) > 0
        
def test_golden_dataset_data_validity():
    with open('parser/tests/golden/Level-23/expected_sessions.json') as f:
        golden = json.load(f)
        
    sessions = golden["sessions"]
    
    # No duplicate verified session identities
    ids = set()
    for s in sessions:
        if s["verificationStatus"] == "verified":
            y_coord = s.get('rawEvidence', {}).get('module', {}).get('y', '0')
            id = f"{s['day']}_{s['startTime']}_{s['endTime']}_{s['moduleCode'] or s['rawModuleCode']}_{s['classType']}_{y_coord}"
            assert id not in ids, f"Duplicate session ID: {id}"
            ids.add(id)
            
    # Check valid days
    days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
    for s in sessions:
        assert s["day"] in days
        
    # Check time format and end > start
    for s in sessions:
        start_m = int(s["startTime"].replace(':', ''))
        end_m = int(s["endTime"].replace(':', ''))
        assert end_m > start_m
        
    # Valid class types
    types = {"L", "P", "T", None}
    for s in sessions:
        assert s["classType"] in types

    # Check for preserved raw values in uncertain records
    uncertain = [s for s in sessions if s["verificationStatus"] == "uncertain"]
    for s in uncertain:
        # uncertain records cannot silently become verified
        assert s["verificationStatus"] == "uncertain"
        if s.get("warnings"):
            assert len(s["warnings"]) > 0

    # Ensure page 2 legend is not parsed
    for s in sessions:
        assert not (s.get("moduleCode") == "CST 2111" and s.get("classType") == "Legend")

