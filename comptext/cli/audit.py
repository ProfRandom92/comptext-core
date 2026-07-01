import sys
import json
import argparse
from pathlib import Path
from comptext.core.plan_validator import validate_execution_log_vs_plan

def run_directory_audit(dir_path: Path, json_output: bool = False) -> None:
    """Audit a directory's structure, entry points, and configuration files."""
    if not dir_path.exists():
        if json_output:
            print(json.dumps({"ok": False, "error": f"Directory not found: {dir_path}"}, indent=2))
        else:
            print(f"Error: Directory not found: {dir_path}", file=sys.stderr)
        sys.exit(1)

    if not dir_path.is_dir():
        if json_output:
            print(json.dumps({"ok": False, "error": f"Path is not a directory: {dir_path}"}, indent=2))
        else:
            print(f"Error: Path is not a directory: {dir_path}", file=sys.stderr)
        sys.exit(1)

    # Scan directory
    structure = []
    entry_points = []
    config_files = []

    # Common entry point filenames
    ENTRY_NAMES = {"main.py", "__main__.py", "run.py", "server.py", "mcp_server.py", "main.rs"}
    # Common config filenames
    CONFIG_NAMES = {"pyproject.toml", "requirements.txt", "config.toml", "Cargo.toml", "setup.py"}

    for p in sorted(dir_path.rglob("*")):
        # Skip common VCS and cache dirs
        if any(part.startswith(".") for part in p.parts) or "__pycache__" in p.parts or "target" in p.parts:
            continue
            
        rel_path = str(p.relative_to(dir_path)).replace("\\", "/")
        structure.append(rel_path)
        
        if p.is_file():
            if p.name in ENTRY_NAMES:
                entry_points.append(rel_path)
            elif p.name in CONFIG_NAMES:
                config_files.append(rel_path)

    if json_output:
        res = {
            "ok": True,
            "directory": str(dir_path.resolve()).replace("\\", "/"),
            "structure": structure,
            "entry_points": entry_points,
            "config_files": config_files
        }
        print(json.dumps(res, indent=2))
    else:
        print("=== CompText Audit Report ===")
        print(f"Directory: {dir_path.resolve()}")
        print("\n[Directory Structure]")
        for item in structure:
            print(f"  - {item}")
        print("\n[Entry Points]")
        for ep in entry_points:
            print(f"  - {ep}")
        print("\n[Configuration Files]")
        for cfg in config_files:
            print(f"  - {cfg}")
        print("=============================")

def main() -> None:
    parser = argparse.ArgumentParser(description="CompText Audit Tool")
    parser.add_argument(
        "--validate-plan",
        help="Path to the registered AIR plan file (JSON)."
    )
    parser.add_argument(
        "--execution-log",
        default="fixtures/evidence/hash-chain.events.json",
        help="Path to the execution log events file (JSON)."
    )
    parser.add_argument(
        "--output-report",
        help="Path to save the validation report JSON file."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        help="Path to the project directory to audit."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output response in JSON format."
    )

    args, unknown = parser.parse_known_args()

    if args.validate_plan:
        plan_path = args.validate_plan
        log_path = args.execution_log
        
        if args.json:
            report = validate_execution_log_vs_plan(plan_path, log_path)
            print(json.dumps(report, indent=2))
            sys.exit(0 if report["status"] == "success" else 1)
        else:
            print(f"Auditing execution log against plan...")
            print(f"  Plan path: {plan_path}")
            print(f"  Log path:  {log_path}")
            report = validate_execution_log_vs_plan(plan_path, log_path)
            if report["status"] == "success":
                print("SUCCESS: Execution log matches plan and hash chain verifies successfully.")
                print(f"  Pipeline steps: {report['satisfied_steps_count']}/{report['pipeline_steps_count']} satisfied.")
                print(f"  Contracts:      {report['satisfied_contracts_count']}/{report['contracts_count']} satisfied.")
                print(f"  Outputs:        {report['satisfied_outputs_count']}/{report['outputs_count']} satisfied.")
                if args.output_report:
                    out_file = Path(args.output_report)
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
                    print(f"  Report written to {args.output_report}")
                sys.exit(0)
            else:
                print(f"AUDIT FAILURE: {report.get('error', 'Unknown validation error')}", file=sys.stderr)
                sys.exit(1)

    elif args.directory:
        run_directory_audit(Path(args.directory), json_output=args.json)
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
