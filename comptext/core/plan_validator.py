import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List
from .crypto import canonical_json

def hash_json_value(data: Any) -> Dict[str, str]:
    """Compute the SHA256 hash of a JSON value in a canonical format."""
    canon = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False
    )
    val = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    return {
        "algorithm": "sha256",
        "canonicalization": "json-c14n-v1",
        "value": val
    }

def hash_event(event: Dict[str, Any]) -> Dict[str, str]:
    """Compute the SHA256 hash of an event, ignoring the event_hash field itself."""
    clone = dict(event)
    clone.pop("event_hash", None)
    return hash_json_value(clone)

def validate_execution_log_vs_plan(plan_path: str, log_path: str) -> Dict[str, Any]:
    """
    Validate that the execution log events satisfy the registered plan constraints.
    Checks:
    - air_ref matches the plan hash
    - event_hash is computed correctly
    - parent_event_hash chains properly
    - all pipeline steps, contracts, and outputs are satisfied
    """
    plan_file = Path(plan_path)
    log_file = Path(log_path)

    if not plan_file.exists():
        return {"status": "failure", "error": f"Plan file not found: {plan_path}"}
    if not log_file.exists():
        return {"status": "failure", "error": f"Log file not found: {log_path}"}

    try:
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
        events = json.loads(log_file.read_text(encoding="utf-8"))
    except Exception as e:
        return {"status": "failure", "error": f"JSON parse error: {str(e)}"}

    plan_hash = hash_json_value(plan_data)

    report = {
        "status": "failure",
        "plan_file": str(plan_file),
        "log_file": str(log_file),
        "plan_hash": plan_hash,
        "event_root_hash": None,
        "pipeline_steps_count": len(plan_data.get("pipeline", [])),
        "satisfied_steps_count": 0,
        "contracts_count": len(plan_data.get("contracts", [])),
        "satisfied_contracts_count": 0,
        "outputs_count": len(plan_data.get("outputs", [])),
        "satisfied_outputs_count": 0
    }

    # Verify event structure and hash chain
    previous_hash = None
    for i, event in enumerate(events):
        # 1. Verify air_ref matches plan hash
        event_air_hash = event.get("air_ref", {}).get("hash", {})
        if event_air_hash != plan_hash:
            return {
                "status": "failure",
                "error": f"Event[{i}] has mismatched air_ref.hash. Expected {plan_hash['value']}, got {event_air_hash.get('value')}"
            }

        # 2. Verify event hash
        actual_hash = hash_event(event)
        if event.get("event_hash") != actual_hash:
            return {
                "status": "failure",
                "error": f"Event[{i}] has invalid event_hash (not recomputed correctly)"
            }

        # 3. Verify parent hash chain
        if i == 0:
            if "parent_event_hash" in event:
                return {"status": "failure", "error": "Event[0] should not have parent_event_hash"}
        else:
            if event.get("parent_event_hash") != previous_hash:
                return {"status": "failure", "error": f"Event[{i}] has mismatched parent_event_hash"}

        previous_hash = event["event_hash"]

    report["event_root_hash"] = previous_hash

    # Verify pipeline steps
    required_steps = plan_data.get("pipeline", [])
    required_steps_set = set(required_steps)
    satisfied_steps = set()

    for event in events:
        action = event.get("action")
        if action in required_steps_set:
            satisfied_steps.add(action)
        
        step_meta = event.get("metadata", {}).get("step")
        if step_meta in required_steps_set:
            satisfied_steps.add(step_meta)
            
        contract_meta = event.get("metadata", {}).get("contract")
        if contract_meta in required_steps_set:
            satisfied_steps.add(contract_meta)

    report["satisfied_steps_count"] = len(satisfied_steps)
    missing_steps = required_steps_set - satisfied_steps
    if missing_steps:
        return {"status": "failure", "error": f"Missing pipeline steps in evidence: {sorted(missing_steps)}"}

    # Verify contracts
    required_contracts = plan_data.get("contracts", [])
    required_contracts_set = set(required_contracts)
    satisfied_contracts = set()

    for event in events:
        action = event.get("action")
        if action in required_contracts_set:
            satisfied_contracts.add(action)

        contract_meta = event.get("metadata", {}).get("contract")
        if contract_meta in required_contracts_set:
            satisfied_contracts.add(contract_meta)

        for output in event.get("outputs", []):
            if output.get("key") in required_contracts_set:
                satisfied_contracts.add(output.get("key"))

    report["satisfied_contracts_count"] = len(satisfied_contracts)
    missing_contracts = required_contracts_set - satisfied_contracts
    if missing_contracts:
        return {"status": "failure", "error": f"Missing contracts in evidence: {sorted(missing_contracts)}"}

    # Verify outputs
    required_outputs = plan_data.get("outputs", [])
    satisfied_outputs = set()

    for output_spec in required_outputs:
        out_path = output_spec.get("path")
        out_kind = output_spec.get("kind")
        
        for event in events:
            for ev_out in event.get("outputs", []):
                key = ev_out.get("key")
                if key == out_path or key == out_kind:
                    satisfied_outputs.add(out_path or out_kind)
            
            if event.get("metadata", {}).get("report") == out_path:
                satisfied_outputs.add(out_path or out_kind)

    report["satisfied_outputs_count"] = len(satisfied_outputs)
    missing_outputs = []
    for o in required_outputs:
        key = o.get("path") or o.get("kind")
        if key not in satisfied_outputs:
            missing_outputs.append(key)

    if missing_outputs:
        return {"status": "failure", "error": f"Missing outputs in evidence: {sorted(missing_outputs)}"}

    report["status"] = "success"
    return report
