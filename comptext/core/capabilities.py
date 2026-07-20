import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

VERSION = "0.1.0"

def get_startup_readiness() -> Dict[str, Any]:
    return {
        "ok": True,
        "command": "startup readiness",
        "schema_version": "0.1",
        "ready_for_review_workflow": True,
        "ready_for_external_execution": False,  # represented as false in JSON
        "contracts": {
            "self_report": True,
            "schema": True,
            "capabilities": True,
            "subagents": True,
            "proposals": True,
            "reviews": True,
            "startup_flow": True,
            "review_workflow": True,
            "validation_runner": True
        },
        "disabled_gates": {
            "network": True,
            "external_agents": True,
            "provider_calls": True,
            "proposal_apply": True,
            "review_apply": True,
            "subagent_execution": True,
            "git_write": True,
            "mcp_server": True,
            "hooks": True,
            "plugins": True
        },
        "recommended_next_commands": [
            "ctxt --json startup flow",
            "ctxt --json self report",
            "ctxt --json schema",
            "ctxt --json capabilities",
            "ctxt --json subagents list",
            "ctxt --json proposals list",
            "ctxt --json reviews list",
            "ctxt --json review workflow",
            "ctxt --json validate --run"
        ],
        "safety": {
            "readiness_executed_commands": False,
            "network_used": False,
            "external_agents_invoked": False,
            "subagents_executed": False,
            "apply_performed": False,
            "git_write_performed": False
        }
    }

def get_startup_flow() -> Dict[str, Any]:
    return {
        "ok": True,
        "command": "startup flow",
        "schema_version": "0.1",
        "execution_supported": False,
        "recommended_sequence": [
            {
                "order": 1,
                "command": "ctxt --json startup readiness",
                "purpose": "confirm deterministic review workflow readiness without enabling external execution",
                "required": True,
                "executes": False
            },
            {
                "order": 2,
                "command": "ctxt --json self report",
                "purpose": "read local runtime baseline and safe entrypoints",
                "required": True,
                "executes": False
            },
            {
                "order": 3,
                "command": "ctxt --json schema",
                "purpose": "read stable JSON command and artifact contracts",
                "required": True,
                "executes": False
            },
            {
                "order": 4,
                "command": "ctxt --json capabilities",
                "purpose": "read supported features and disabled gates",
                "required": True,
                "executes": False
            },
            {
                "order": 5,
                "command": "ctxt --json subagents list",
                "purpose": "read deterministic review and planning role contracts",
                "required": True,
                "executes": False
            },
            {
                "order": 6,
                "command": "ctxt --json proposals list",
                "purpose": "list local proposal artifact references without applying them",
                "required": True,
                "executes": False
            },
            {
                "order": 7,
                "command": "ctxt --json reviews list",
                "purpose": "list local review artifact references without generating or applying reviews",
                "required": True,
                "executes": False
            },
            {
                "order": 8,
                "command": "ctxt --json review workflow",
                "purpose": "read deterministic review workflow checklist without executing it",
                "required": True,
                "executes": False
            },
            {
                "order": 9,
                "command": "ctxt --json validate --run",
                "purpose": "run local validation only when the phase permits validation execution",
                "required": True,
                "executes": False
            }
        ]
    }

def get_capabilities() -> Dict[str, Any]:
    return {
        "ok": True,
        "command": "capabilities",
        "schema_version": "0.1",
        "phases": [
            {"phase": "1", "name": "local runtime", "status": "stable"},
            {"phase": "2", "name": "execution-plan-only", "status": "stable"},
            {"phase": "3", "name": "discovery-only", "status": "stable"},
            {"phase": "4a", "name": "companion skill", "status": "stable"},
            {"phase": "4b", "name": "agent-friendly CLI polish", "status": "stable"},
            {"phase": "4c", "name": "JSON schema contract", "status": "stable"},
            {"phase": "4d", "name": "cross-agent guidance", "status": "stable"},
            {"phase": "4e", "name": "runtime self report", "status": "stable"},
            {"phase": "4f", "name": "proposal artifact contract", "status": "stable"},
            {"phase": "4g", "name": "proposal schema contracts", "status": "stable"},
            {"phase": "4h", "name": "proposal capabilities", "status": "stable"},
            {"phase": "5a", "name": "deterministic subagent role contract", "status": "stable"},
            {"phase": "5b", "name": "deterministic review artifact contract", "status": "stable"},
            {"phase": "5c", "name": "deterministic startup review flow contract", "status": "stable"},
            {"phase": "5d", "name": "deterministic startup readiness contract", "status": "stable"},
            {"phase": "5e", "name": "deterministic review workflow contract", "status": "stable"}
        ],
        "safety": {
            "network_default": "deny",
            "external_agents_invoked": False,
            "apply_automatic": False,
            "proposal_required": True
        },
        "features": {
            "agent_list": True,
            "agent_discovery": True,
            "execution_plan_only": True,
            "runs_list": True,
            "runs_read": True,
            "proposals_list": True,
            "proposals_inspect": True,
            "proposals_validate": True,
            "proposal_artifact_contract": True,
            "subagent_role_contract": True,
            "subagent_execution": False,
            "subagent_runtime_orchestration": False,
            "reviews_list": True,
            "reviews_inspect": True,
            "reviews_validate": True,
            "review_artifact_contract": True,
            "review_workflow_execution": False,
            "reproducible_rng": True
        },
        "commands": [
            "startup readiness",
            "startup flow",
            "self report",
            "schema",
            "capabilities",
            "subagents list",
            "proposals list",
            "reviews list",
            "review workflow",
            "validate"
        ]
    }

def get_schema() -> Dict[str, Any]:
    return {
        "ok": True,
        "command": "schema",
        "schema_version": "0.1",
        "contracts": [
            {
                "command": "capabilities",
                "status": "stable",
                "required_fields": [
                    "ok",
                    "command",
                    "schema_version",
                    "phases",
                    "safety",
                    "features",
                    "commands"
                ],
                "notes": ["read-only", "no network", "no external agents"]
            },
            {
                "command": "runs list",
                "status": "stable",
                "required_fields": ["ok", "command", "schema_version", "runs"],
                "run_fields": ["id", "path", "exists"],
                "notes": ["read-only"]
            },
            {
                "command": "runs read",
                "status": "stable",
                "required_fields": [
                    "ok",
                    "command",
                    "schema_version",
                    "id",
                    "path",
                    "kind",
                    "max_bytes",
                    "truncated",
                    "content"
                ],
                "notes": ["bounded read", "read-only"]
            },
            {
                "command": "proposals list",
                "status": "stable",
                "notes": [
                    "read-only",
                    "local proposals directory only",
                    "malformed JSON remains listable with valid=false",
                    "no apply",
                    "no network",
                    "no external agents"
                ],
                "required_fields": ["ok", "command", "schema_version", "proposals", "count"],
                "proposal_fields": [
                    "id",
                    "path",
                    "created_at",
                    "phase",
                    "title",
                    "status",
                    "valid"
                ]
            },
            {
                "command": "proposals inspect",
                "status": "stable",
                "notes": [
                    "bounded read",
                    "read-only",
                    "latest resolves lexicographically",
                    "no apply",
                    "no network",
                    "no external agents"
                ],
                "required_fields": [
                    "ok",
                    "command",
                    "schema_version",
                    "id",
                    "path",
                    "kind",
                    "max_bytes",
                    "truncated",
                    "content"
                ]
            },
            {
                "command": "proposals validate",
                "status": "stable",
                "notes": [
                    "read-only",
                    "re-verifies proposal contract constraints",
                    "no apply",
                    "no network"
                ],
                "required_fields": [
                    "ok",
                    "command",
                    "schema_version",
                    "id",
                    "valid",
                    "errors"
                ]
            },
            {
                "command": "reviews list",
                "status": "stable",
                "notes": [
                    "read-only",
                    "local reviews directory only",
                    "malformed JSON remains listable with valid=false",
                    "no generation",
                    "no apply",
                    "no network",
                    "no external agents"
                ],
                "required_fields": ["ok", "command", "schema_version", "reviews", "count"],
                "review_fields": [
                    "id",
                    "path",
                    "created_at",
                    "phase",
                    "role_id",
                    "target",
                    "status",
                    "valid"
                ]
            },
            {
                "command": "reviews inspect",
                "status": "stable",
                "notes": [
                    "bounded read",
                    "read-only",
                    "latest resolves lexicographically",
                    "no generation",
                    "no apply",
                    "no network",
                    "no external agents"
                ],
                "required_fields": [
                    "ok",
                    "command",
                    "schema_version",
                    "id",
                    "path",
                    "kind",
                    "max_bytes",
                    "truncated",
                    "content"
                ]
            },
            {
                "command": "reviews validate",
                "status": "stable",
                "notes": [
                    "read-only",
                    "re-verifies review contract constraints",
                    "no generation",
                    "no apply",
                    "no network"
                ],
                "required_fields": [
                    "ok",
                    "command",
                    "schema_version",
                    "id",
                    "valid",
                    "errors"
                ]
            }
        ]
    }

def get_self_report() -> Dict[str, Any]:
    return {
        "ok": True,
        "command": "self report",
        "schema_version": "0.1",
        "runtime": {
            "name": "ctxt",
            "version": VERSION,
            "phase": "4e",
            "mode": "cross-agent-safe"
        },
        "toolchain": {
            "rust_required": "stable",
            "rust_validated": "1.96.0"
        },
        "validation": {
            "source_of_truth": "external PowerShell on this Windows machine",
            "last_known_unit_tests": 37,
            "last_known_smoke_tests": 39,
            "validate_run_green": True
        },
        "safe_entrypoints": [
            "ctxt --json schema",
            "ctxt --json startup readiness",
            "ctxt --json startup flow",
            "ctxt --json review workflow",
            "ctxt --json capabilities",
            "ctxt --json subagents list",
            "ctxt --json reviews list",
            "ctxt --json reviews inspect latest --max-bytes 12000",
            "ctxt --json reviews validate latest",
            "ctxt --json runs list",
            "ctxt --json runs read latest --max-bytes 12000",
            "ctxt --json agent discover",
            "ctxt --json validate --run"
        ],
        "agent_policy": {
            "codex_direct_task_execution": False,
            "antigravity_direct_task_execution": False,
            "proposal_only": True,
            "external_execution": False,
            "subagent_execution": False,
            "subagent_roles_contract_only": True,
            "review_generation": False,
            "review_apply": False,
            "review_artifacts_contract_only": True,
            "startup_flow_execution": False,
            "startup_flow_contract_only": True,
            "startup_readiness_execution": False,
            "startup_readiness_contract_only": True,
            "ready_for_review_workflow": True,
            "ready_for_external_execution": False,
            "review_workflow_execution": False,
            "review_workflow_contract_only": True,
            "review_workflow_apply": False,
            "network_default": "deny",
            "apply_automatic": False
        }
    }

def get_subagents_list() -> Dict[str, Any]:
    forbidden = [
        "network",
        "providers",
        "external_agent_invocation",
        "proposal_apply",
        "git_write",
        "runtime_execution",
    ]
    roles = [
        ("schema-reviewer", "Schema Reviewer"),
        ("capabilities-reviewer", "Capabilities Reviewer"),
        ("proposal-reviewer", "Proposal Reviewer"),
        ("test-reviewer", "Test Reviewer"),
        ("docs-reviewer", "Docs Reviewer"),
        ("safety-reviewer", "Safety Reviewer"),
    ]
    roles_list = []
    for r_id, name in roles:
        roles_list.append({
            "id": r_id,
            "name": name,
            "mode": "contract-only",
            "allowed_outputs": ["finding", "risk", "recommendation"],
            "may_edit_files": False,
            "may_run_commands": False,
            "forbidden": forbidden
        })
    return {
        "ok": True,
        "command": "subagents list",
        "schema_version": "0.1",
        "execution_supported": False,
        "roles": roles_list,
        "safety": {
            "subagents_executed": False,
            "external_agents_invoked": False,
            "network_used": False,
            "apply_performed": False,
            "git_write_performed": False
        }
    }

def get_review_workflow() -> Dict[str, Any]:
    return {
        "ok": True,
        "command": "review workflow",
        "schema_version": "0.1",
        "execution_supported": False,
        "workflow_kind": "deterministic-review",
        "required_contracts": {
            "startup_readiness": True,
            "startup_flow": True,
            "subagent_roles": True,
            "proposal_artifacts": True,
            "review_artifacts": True,
            "validation_runner": True,
            "schema": True,
            "capabilities": True,
            "self_report": True
        },
        "workflow_steps": [
            {
                "order": 1,
                "id": "startup-readiness",
                "command": "ctxt --json startup readiness",
                "purpose": "confirm deterministic review workflow readiness",
                "required": True,
                "executes": False,
                "applies_changes": False
            },
            {
                "order": 2,
                "id": "startup-flow",
                "command": "ctxt --json startup flow",
                "purpose": "read the safe startup checklist",
                "required": True,
                "executes": False,
                "applies_changes": False
            },
            {
                "order": 3,
                "id": "inspect-schema",
                "command": "ctxt --json schema",
                "purpose": "inspect stable JSON contracts",
                "required": True,
                "executes": False,
                "applies_changes": False
            },
            {
                "order": 4,
                "id": "inspect-capabilities",
                "command": "ctxt --json capabilities",
                "purpose": "inspect available features and disabled gates",
                "required": True,
                "executes": False,
                "applies_changes": False
            },
            {
                "order": 5,
                "id": "inspect-subagent-roles",
                "command": "ctxt --json subagents list",
                "purpose": "inspect deterministic reviewer role contracts",
                "required": True,
                "executes": False,
                "applies_changes": False
            },
            {
                "order": 6,
                "id": "list-proposals",
                "command": "ctxt --json proposals list",
                "purpose": "list local proposal artifact references",
                "required": True,
                "executes": False,
                "applies_changes": False
            },
            {
                "order": 7,
                "id": "validate-target-proposal",
                "command": "ctxt --json proposals validate latest",
                "purpose": "validate the selected proposal artifact contract when permitted",
                "required": True,
                "executes": False,
                "applies_changes": False
            },
            {
                "order": 8,
                "id": "list-reviews",
                "command": "ctxt --json reviews list",
                "purpose": "list local review artifact references",
                "required": True,
                "executes": False,
                "applies_changes": False
            },
            {
                "order": 9,
                "id": "validate-target-review",
                "command": "ctxt --json reviews validate latest",
                "purpose": "validate the selected review artifact contract when permitted",
                "required": True,
                "executes": False,
                "applies_changes": False
            },
            {
                "order": 10,
                "id": "run-local-validation",
                "command": "ctxt --json validate --run",
                "purpose": "run local validation only when the active phase permits it",
                "required": True,
                "executes": False,
                "applies_changes": False
            },
            {
                "order": 11,
                "id": "summarize-findings-for-user",
                "command": "user-facing summary only",
                "purpose": "summarize findings, risks, and validation evidence for the user",
                "required": True,
                "executes": False,
                "applies_changes": False
            }
        ],
        "required_roles": [
            "schema-reviewer",
            "capabilities-reviewer",
            "proposal-reviewer",
            "test-reviewer",
            "docs-reviewer",
            "safety-reviewer"
        ],
        "evidence_inputs": [
            "proposal artifacts",
            "review artifacts",
            "validation output",
            "schema output",
            "capabilities output",
            "self report output"
        ],
        "forbidden_actions": [
            "network",
            "providers",
            "external_agent_invocation",
            "codex_cli_invocation",
            "antigravity_cli_invocation",
            "subagent_runtime_execution",
            "proposal_apply",
            "review_apply",
            "git_write",
            "mcp_server",
            "hooks",
            "plugins",
            "arbitrary_shell_execution"
        ],
        "safety": {
            "workflow_executed": False,
            "network_used": False,
            "external_agents_invoked": False,
            "subagents_executed": False,
            "apply_performed": False,
            "git_write_performed": False
        }
    }

def is_safe_proposal_id(id_str: str) -> bool:
    if not id_str or id_str.startswith('.') or '..' in id_str or '/' in id_str or '\\' in id_str:
        return False
    return all(c.isdigit() or c.islower() or c in ('T', 'Z', '-') for c in id_str)

def is_safe_review_id(id_str: str) -> bool:
    return is_safe_proposal_id(id_str)

def list_proposal_files(proposals_dir: str = "proposals") -> List[Tuple[str, str, Path]]:
    root = Path(proposals_dir)
    if not root.exists() or not root.is_dir():
        return []

    files = []
    for item in root.iterdir():
        if item.is_file() and item.suffix == ".json":
            stem = item.stem
            rel_path = f"{proposals_dir}/{stem}.json"
            files.append((stem, rel_path, item))
    files.sort(key=lambda x: x[0])
    return files

def list_review_files(reviews_dir: str = "reviews") -> List[Tuple[str, str, Path]]:
    root = Path(reviews_dir)
    if not root.exists() or not root.is_dir():
        return []

    files = []
    for item in root.iterdir():
        if item.is_file() and item.name.endswith(".review.json"):
            stem = item.name[:-12]  # strip .review.json
            rel_path = f"{reviews_dir}/{item.name}"
            files.append((stem, rel_path, item))
    files.sort(key=lambda x: x[0])
    return files

def validate_proposal_contract(data: Any, filename_id: str) -> List[str]:
    errors = []
    if not isinstance(data, dict):
        return ["proposal must be a JSON object"]

    if not is_safe_proposal_id(filename_id):
        errors.append(f"filename stem '{filename_id}' is not a safe proposal id")

    schema_version = data.get("schema_version")
    if schema_version != "proposal.v1":
        errors.append("schema_version must be 'proposal.v1'")

    embedded_id = data.get("id")
    if embedded_id != filename_id:
        errors.append("proposal id must match filename stem")

    for field in ["created_at", "phase", "title", "summary", "intent", "secrets"]:
        val = data.get(field)
        if not isinstance(val, str):
            errors.append(f"field '{field}' must be a string")

    for field in ["allowed_files", "forbidden_scope", "validation"]:
        val = data.get(field)
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            errors.append(f"field '{field}' must be an array of strings")

    network = data.get("network")
    if network not in ("offline-only", "local-only", "allowed-external"):
        errors.append("network must be one of offline-only, local-only, allowed-external")

    status = data.get("status")
    if status not in ("draft", "ready-for-review", "rejected", "approved-for-apply"):
        errors.append("status must be one of draft, ready-for-review, rejected, approved-for-apply")

    changes = data.get("changes")
    if isinstance(changes, list):
        for index, change in enumerate(changes):
            if not isinstance(change, dict):
                errors.append(f"changes[{index}] must be an object")
                continue
            for f in ["path", "summary"]:
                if not isinstance(change.get(f), str):
                    errors.append(f"changes[{index}].{f} must be a string")
            action = change.get("action")
            if action not in ("add", "modify", "delete", "rename", "document"):
                errors.append(f"changes[{index}].action must be one of add, modify, delete, rename, document")
    else:
        errors.append("field 'changes' must be an array of objects")

    return errors

def validate_review_contract(data: Any, filename_id: str) -> List[str]:
    errors = []
    if not isinstance(data, dict):
        return ["review must be a JSON object"]

    if not is_safe_review_id(filename_id):
        errors.append(f"filename id '{filename_id}' is not a safe review id")

    schema_version = data.get("schema_version")
    if schema_version != "review.v1":
        errors.append("schema_version must be 'review.v1'")

    embedded_id = data.get("id")
    if embedded_id != filename_id:
        errors.append("review id must match filename-derived id")

    for field in ["created_at", "phase", "target", "summary"]:
        val = data.get(field)
        if not isinstance(val, str):
            errors.append(f"field '{field}' must be a string")

    role_id = data.get("role_id")
    allowed_roles = [
        "schema-reviewer",
        "capabilities-reviewer",
        "proposal-reviewer",
        "test-reviewer",
        "docs-reviewer",
        "safety-reviewer",
    ]
    if role_id not in allowed_roles:
        errors.append("role_id must be one of the allowed subagent role ids")

    val_refs = data.get("validation_refs")
    if not isinstance(val_refs, list) or not all(isinstance(x, str) for x in val_refs):
        errors.append("field 'validation_refs' must be an array of strings")

    def validate_items(field_name: str, enum_field: str, allowed_vals: List[str]):
        items = data.get(field_name)
        if isinstance(items, list):
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"{field_name}[{index}] must be an object")
                    continue
                for f in ["id", "summary"]:
                    if not isinstance(item.get(f), str):
                        errors.append(f"{field_name}[{index}].{f} must be a string")
                val = item.get(enum_field)
                if val not in allowed_vals:
                    errors.append(f"{field_name}[{index}].{enum_field} must be one of {', '.join(allowed_vals)}")
        else:
            errors.append(f"field '{field_name}' must be an array of objects")

    validate_items("findings", "severity", ["info", "low", "medium", "high"])
    validate_items("risks", "severity", ["low", "medium", "high"])
    validate_items("recommendations", "action", ["keep", "fix", "defer", "reject"])

    # validate safety_flags
    flags = data.get("safety_flags")
    if isinstance(flags, dict):
        expected_flags = [
            "network_used",
            "external_agents_invoked",
            "subagents_executed",
            "apply_performed",
            "git_write_performed",
            "secrets_accessed",
        ]
        for field in expected_flags:
            val = flags.get(field)
            if not isinstance(val, bool):
                errors.append(f"safety_flags.{field} must be a boolean")
            elif val is True:
                errors.append(f"safety_flags.{field} must be false")
    else:
        errors.append("field 'safety_flags' must be an object")

    status = data.get("status")
    if status not in ("draft", "ready-for-review", "accepted", "rejected"):
        errors.append("status must be one of draft, ready-for-review, accepted, rejected")

    return errors

def get_proposals_list_report(proposals_dir: str = "proposals") -> Dict[str, Any]:
    proposals = []
    files = list_proposal_files(proposals_dir)
    for stem, rel_path, path in files:
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
            errors = validate_proposal_contract(parsed, stem)
        except Exception:
            parsed = None
            errors = ["proposal JSON is malformed"]

        proposals.append({
            "id": stem,
            "path": rel_path,
            "created_at": parsed.get("created_at") if parsed else None,
            "phase": parsed.get("phase") if parsed else None,
            "title": parsed.get("title") if parsed else None,
            "status": parsed.get("status") if parsed else None,
            "valid": len(errors) == 0
        })
    return {
        "ok": True,
        "command": "proposals list",
        "schema_version": "0.1",
        "proposals": proposals,
        "count": len(proposals)
    }

def get_reviews_list_report(reviews_dir: str = "reviews") -> Dict[str, Any]:
    reviews = []
    files = list_review_files(reviews_dir)
    for stem, rel_path, path in files:
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
            errors = validate_review_contract(parsed, stem)
        except Exception:
            parsed = None
            errors = ["review JSON is malformed"]

        reviews.append({
            "id": stem,
            "path": rel_path,
            "created_at": parsed.get("created_at") if parsed else None,
            "phase": parsed.get("phase") if parsed else None,
            "role_id": parsed.get("role_id") if parsed else None,
            "target": parsed.get("target") if parsed else None,
            "status": parsed.get("status") if parsed else None,
            "valid": len(errors) == 0
        })
    return {
        "ok": True,
        "command": "reviews list",
        "schema_version": "0.1",
        "reviews": reviews,
        "count": len(reviews)
    }

def validation_commands() -> List[str]:
    return ["python -m pytest"]

def validation_commands_for_run() -> List[str]:
    env_val = os.environ.get("CTXT_VALIDATE_COMMANDS_FOR_TEST")
    if env_val and env_val.strip():
        return [line.strip() for line in env_val.strip().splitlines() if line.strip()]
    return validation_commands()

def run_validation_step(cmd_str: str) -> Dict[str, Any]:
    import shlex
    import subprocess
    try:
        parts = shlex.split(cmd_str)
    except Exception:
        parts = cmd_str.split()

    if not parts:
        return {"cmd": cmd_str, "ok": False, "exit_code": -1, "error": "empty validation command"}

    env = dict(os.environ)
    env["CTXT_VALIDATE_INNER"] = "1"

    executable = parts[0]
    _, ext = os.path.splitext(executable.lower())
    if ext in {".cmd", ".bat", ".ps1", ".vbs", ".js", ".wsf"}:
        return {
            "cmd": cmd_str,
            "ok": False,
            "exit_code": -1,
            "stderr_excerpt": f"Security Policy Violation: script execution of extension '{ext}' is forbidden."
        }

    try:
        res = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            env=env,
            shell=False
        )
        return {
            "cmd": cmd_str,
            "ok": res.returncode == 0,
            "exit_code": res.returncode,
            "stdout_excerpt": res.stdout[:4096] if res.stdout else "",
            "stderr_excerpt": res.stderr[:4096] if res.stderr else ""
        }
    except Exception as e:
        return {
            "cmd": cmd_str,
            "ok": False,
            "exit_code": -1,
            "stdout_excerpt": "",
            "stderr_excerpt": str(e)
        }

def run_validation_flow(run: bool) -> Dict[str, Any]:
    if not run:
        return {
            "ok": True,
            "command": "validate",
            "run": False,
            "validation_commands": validation_commands()
        }

    commands = validation_commands_for_run()
    steps = []
    failed_step = None

    for command in commands:
        step = run_validation_step(command)
        steps.append(step)
        if not step["ok"]:
            failed_step = command
            break

    payload = {
        "command": "validate",
        "run": True,
        "ok": failed_step is None,
        "steps": steps
    }
    if failed_step:
        payload["failed_step"] = failed_step
    return payload
