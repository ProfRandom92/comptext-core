import json
from comptext.core.plan_validator import validate_execution_log_vs_plan

def test_plan_validator_success():
    plan_path = "tests/fixtures/air/hash-chain.audit.air.json"
    log_path = "tests/fixtures/evidence/hash-chain.events.json"
    
    report = validate_execution_log_vs_plan(plan_path, log_path)
    assert report["status"] == "success"
    assert report["pipeline_steps_count"] == report["satisfied_steps_count"]
    assert report["contracts_count"] == report["satisfied_contracts_count"]
    assert report["outputs_count"] == report["satisfied_outputs_count"]

def test_plan_validator_tampered_hash(tmp_path):
    plan_path = "tests/fixtures/air/hash-chain.audit.air.json"
    log_path = "tests/fixtures/evidence/hash-chain.events.json"
    
    # Load events and mutate one
    with open(log_path, "r", encoding="utf-8") as f:
        events = json.load(f)
    
    # Tamper with the first event's action
    events[0]["action"] = "tampered_action"
    
    temp_log = tmp_path / "tampered_events.json"
    with open(temp_log, "w", encoding="utf-8") as f:
        json.dump(events, f)
        
    report = validate_execution_log_vs_plan(plan_path, str(temp_log))
    assert report["status"] == "failure"
    assert "invalid event_hash" in report["error"]

def test_directory_audit(tmp_path):
    from comptext.cli.audit import run_directory_audit
    (tmp_path / "main.py").touch()
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "other.txt").touch()
    
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        run_directory_audit(tmp_path, json_output=True)
        output = json.loads(sys.stdout.getvalue())
    finally:
        sys.stdout = old_stdout
        
    assert output["ok"] is True
    assert "main.py" in output["entry_points"]
    assert "pyproject.toml" in output["config_files"]
    assert "other.txt" in output["structure"]
