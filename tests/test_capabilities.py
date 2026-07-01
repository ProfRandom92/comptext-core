import json
import pytest
from pathlib import Path
from comptext.core.capabilities import (
    get_startup_readiness,
    get_startup_flow,
    get_capabilities,
    get_schema,
    get_self_report,
    get_subagents_list,
    get_review_workflow,
    list_proposal_files,
    validate_proposal_contract,
    validate_review_contract,
    get_proposals_list_report,
    get_reviews_list_report,
)

def test_capabilities_reports():
    readiness = get_startup_readiness()
    assert readiness["ok"] is True
    assert readiness["command"] == "startup readiness"
    assert "contracts" in readiness
    assert "disabled_gates" in readiness

    flow = get_startup_flow()
    assert flow["ok"] is True
    assert flow["command"] == "startup flow"
    assert len(flow["recommended_sequence"]) > 0

    caps = get_capabilities()
    assert caps["ok"] is True
    assert len(caps["phases"]) > 0
    assert caps["safety"]["network_default"] == "deny"

    schema = get_schema()
    assert schema["ok"] is True
    assert len(schema["contracts"]) > 0

    report = get_self_report()
    assert report["ok"] is True
    assert report["runtime"]["name"] == "ctxt"

    subagents = get_subagents_list()
    assert subagents["ok"] is True
    assert len(subagents["roles"]) > 0

    workflow = get_review_workflow()
    assert workflow["ok"] is True
    assert len(workflow["workflow_steps"]) > 0

def test_proposal_validation():
    # Test valid proposal fixture
    prop_path = Path("tests/fixtures/proposals/20260613T120000Z-phase-4f-example.json")
    assert prop_path.exists()
    
    parsed = json.loads(prop_path.read_text(encoding="utf-8"))
    errors = validate_proposal_contract(parsed, prop_path.stem)
    assert errors == []

    # Test invalid proposal
    invalid_prop = parsed.copy()
    invalid_prop["schema_version"] = "invalid"
    errors = validate_proposal_contract(invalid_prop, prop_path.stem)
    assert len(errors) > 0
    assert any("schema_version" in e for e in errors)

def test_list_proposal_files():
    files = list_proposal_files("tests/fixtures/proposals")
    assert len(files) == 1
    stem, rel_path, path = files[0]
    assert stem == "20260613T120000Z-phase-4f-example"
    assert rel_path == "tests/fixtures/proposals/20260613T120000Z-phase-4f-example.json"

def test_proposals_list_report():
    report = get_proposals_list_report("tests/fixtures/proposals")
    assert report["ok"] is True
    assert report["count"] == 1
    assert report["proposals"][0]["id"] == "20260613T120000Z-phase-4f-example"
    assert report["proposals"][0]["valid"] is True
