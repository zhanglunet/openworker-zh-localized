GATE_ALLOWED = "MATCH"
REFUSED = "REPLAY_GATE_REFUSED"

def replay_gate(verify_result):
    if not isinstance(verify_result, dict) or "status" not in verify_result:
        return {"allow": False, "code": REFUSED, "evidence": "missing"}
    if verify_result["status"] == GATE_ALLOWED:
        return {"allow": True, "code": None, "status": "MATCH"}
    return {"allow": False, "code": REFUSED, "status": verify_result["status"],
            "evidence": verify_result.get("evidence")}
