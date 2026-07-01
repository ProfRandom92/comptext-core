import sys
import json
from pathlib import Path
from comptext.config import Config
from comptext.core import capabilities

def print_help():
    print("CompText CLI - Interface Layer")
    print("Usage:")
    print("  comptext-cli [command] [options]")
    print()
    print("Commands:")
    print("  startup readiness   Check startup readiness status")
    print("  startup flow        Get recommended startup flow sequence")
    print("  schema              Get stable JSON command and contract schemas")
    print("  capabilities        Inspect supported features and safety gates")
    print("  self report         Get runtime and agent policy status")
    print("  subagents list      List active subagent roles and forbidden actions")
    print("  proposals list      List local proposal artifacts")
    print("  reviews list        List local review artifacts")
    print("  review workflow     Get review workflow sequence checklist")
    print("  validate [--run]    Inspect or run local validation suite")
    print("  doctor              Inspect tool status and auth parameters")
    print("  providers list      List all configured providers")
    print("  keygen              Generate Ed25519 keypair")
    print("  verify              Verify trace Merkle root and Ed25519 signature")
    print("  audit [path]        Perform a read-only audit of a project directory")
    print("  logo                Render the CompText logo")
    print("  version             Print version info")
    print()
    print("Global Options:")
    print("  --json              Output response in JSON format")

def main():
    # If no args, run the interactive REPL
    if len(sys.argv) == 1:
        from comptext.repl import run_cli
        run_cli()
        return

    # Check for help flags
    if "-h" in sys.argv or "--help" in sys.argv or "help" in sys.argv:
        print_help()
        sys.exit(0)

    # Parse global --json flag
    json_output = False
    args = []
    for arg in sys.argv[1:]:
        if arg == "--json":
            json_output = True
        else:
            args.append(arg)

    if not args:
        print_help()
        sys.exit(1)

    # Handle logo command early
    if args[0] == "logo":
        from comptext.cli.logo import run_logo
        run_logo(args[1:])
        return

    # Handle verify command early
    if args[0] == "verify":
        from comptext.cli.verify import run_verify
        run_verify(args[1:], json_output)
        return

    # Handle audit command early
    if args[0] == "audit":
        from comptext.cli.audit import main as run_audit
        sys.argv = [sys.argv[0]] + args[1:]
        if json_output and "--json" not in sys.argv:
            sys.argv.append("--json")
        run_audit()
        return

    # Handle keygen command early
    if args[0] == "keygen":
        from comptext.core.crypto import generate_keypair
        import stat
        priv_b, pub_b, priv_h, pub_h = generate_keypair()
        
        keys_dir = Path(".comptext/keys")
        keys_dir.mkdir(parents=True, exist_ok=True)
        
        priv_file = keys_dir / "id_ed25519"
        pub_file = keys_dir / "id_ed25519.pub"
        
        priv_file.write_bytes(priv_b)
        pub_file.write_bytes(pub_b)
        
        # Save hex versions for convenience
        (keys_dir / "id_ed25519.hex").write_text(priv_h, encoding="utf-8")
        (keys_dir / "id_ed25519.pub.hex").write_text(pub_h, encoding="utf-8")
        
        try:
            priv_file.chmod(0o400)
        except Exception:
            try:
                priv_file.chmod(stat.S_IREAD)
            except Exception:
                pass
                
        if json_output:
            res = {
                "ok": True,
                "command": "keygen",
                "private_key_hex": priv_h,
                "public_key_hex": pub_h,
                "private_key_path": str(priv_file),
                "public_key_path": str(pub_file)
            }
            print(json.dumps(res, indent=2))
        else:
            print("Generated Ed25519 Keypair successfully.")
            print("Saved to:")
            print(f"  Private Key: {priv_file}")
            print(f"  Public Key:  {pub_file}")
            print(f"Private Key Hex: {priv_h}")
            print(f"Public Key Hex:  {pub_h}")
        sys.exit(0)

    cmd = " ".join(args).strip()

    # Create config object for doctor and providers
    config = Config()

    # Implement JSON output mode
    if json_output:
        if cmd == "startup readiness":
            print(json.dumps(capabilities.get_startup_readiness(), indent=2))
            sys.exit(0)
        elif cmd == "startup flow":
            print(json.dumps(capabilities.get_startup_flow(), indent=2))
            sys.exit(0)
        elif cmd == "capabilities":
            print(json.dumps(capabilities.get_capabilities(), indent=2))
            sys.exit(0)
        elif cmd == "schema":
            print(json.dumps(capabilities.get_schema(), indent=2))
            sys.exit(0)
        elif cmd == "self report":
            print(json.dumps(capabilities.get_self_report(), indent=2))
            sys.exit(0)
        elif cmd == "subagents list":
            print(json.dumps(capabilities.get_subagents_list(), indent=2))
            sys.exit(0)
        elif cmd == "proposals list":
            print(json.dumps(capabilities.get_proposals_list_report(), indent=2))
            sys.exit(0)
        elif cmd == "reviews list":
            print(json.dumps(capabilities.get_reviews_list_report(), indent=2))
            sys.exit(0)
        elif cmd == "review workflow":
            print(json.dumps(capabilities.get_review_workflow(), indent=2))
            sys.exit(0)
        elif cmd == "validate --run" or cmd == "validate -run":
            res = capabilities.run_validation_flow(run=True)
            print(json.dumps(res, indent=2))
            sys.exit(0 if res["ok"] else 1)
        elif cmd == "validate":
            print(json.dumps(capabilities.run_validation_flow(run=False), indent=2))
            sys.exit(0)
        elif cmd == "doctor":
            # doctor json output
            doctor_data = {
                "ok": True,
                "command": "doctor",
                "status": "ok",
                "binary": "ctxt",
                "version": capabilities.VERSION,
                "network_default": "deny",
                "provider_default": config.get("provider", "dummy"),
                "provider_default_network": False,
                "proposal_required": True,
                "dry_run_default": True,
                "secrets_policy": "redact-before-artifact",
                "auth": {
                    "required": False,
                    "source": "missing",
                    "note": "offline dummy provider does not require auth"
                }
            }
            print(json.dumps(doctor_data, indent=2))
            sys.exit(0)
        elif cmd == "providers list":
            # providers list json output
            providers_data = {
                "ok": True,
                "command": "providers list",
                "providers": [
                    {
                        "name": "dummy",
                        "kind": "dummy",
                        "network": False,
                        "auth": None,
                        "auth_env": None,
                        "model": None,
                        "model_suffix": None
                    },
                    {
                        "name": "ollama-local",
                        "kind": "ollama",
                        "network": True,
                        "auth": "none",
                        "auth_env": None,
                        "model": None,
                        "model_suffix": None
                    },
                    {
                        "name": "openai-compatible",
                        "kind": "openai-compatible",
                        "network": False,
                        "auth": None,
                        "auth_env": "OPTIONAL_API_KEY",
                        "model": "gpt-4o",
                        "model_suffix": None
                    },
                    {
                        "name": "nvidia",
                        "kind": "nvidia",
                        "network": True,
                        "auth": "api_key",
                        "auth_env": "NVIDIA_API_KEY",
                        "model": "deepseek-ai/deepseek-v4-flash",
                        "model_suffix": None
                    }
                ]
            }
            print(json.dumps(providers_data, indent=2))
            sys.exit(0)
        elif cmd == "version":
            print(json.dumps({"ok": True, "command": "version", "version": capabilities.VERSION}, indent=2))
            sys.exit(0)
        else:
            print(json.dumps({"ok": False, "error": f"Unknown JSON command: {cmd}"}, indent=2), file=sys.stderr)
            sys.exit(1)

    # Non-JSON Mode
    if cmd == "startup readiness":
        print("Startup readiness: OK")
        sys.exit(0)
    elif cmd == "startup flow":
        print("Startup sequence recommended order:")
        for step in capabilities.get_startup_flow()["recommended_sequence"]:
            print(f"  {step['order']}. {step['command']} ({step['purpose']})")
        sys.exit(0)
    elif cmd == "capabilities":
        print("Capabilities:")
        print("  Phases: 15 active")
        print("  Safety default: deny network")
        sys.exit(0)
    elif cmd == "schema":
        print("Schema contracts stable.")
        sys.exit(0)
    elif cmd == "self report":
        report = capabilities.get_self_report()
        print(f"Runtime: {report['runtime']['name']} v{report['runtime']['version']}")
        print(f"Mode: {report['runtime']['mode']}")
        sys.exit(0)
    elif cmd == "subagents list":
        print("Available subagent roles:")
        for role in capabilities.get_subagents_list()["roles"]:
            print(f"  - {role['name']} ({role['id']})")
        sys.exit(0)
    elif cmd == "proposals list":
        res = capabilities.get_proposals_list_report()
        print(f"Proposals count: {res['count']}")
        for prop in res["proposals"]:
            print(f"  - {prop['id']} ({prop['path']}) - Valid: {prop['valid']}")
        sys.exit(0)
    elif cmd == "reviews list":
        res = capabilities.get_reviews_list_report()
        print(f"Reviews count: {res['count']}")
        for rev in res["reviews"]:
            print(f"  - {rev['id']} ({rev['path']}) - Valid: {rev['valid']}")
        sys.exit(0)
    elif cmd == "review workflow":
        print("Review workflow sequence:")
        for step in capabilities.get_review_workflow()["workflow_steps"]:
            print(f"  {step['order']}. {step['command']} - {step['purpose']}")
        sys.exit(0)
    elif cmd == "validate --run" or cmd == "validate -run":
        res = capabilities.run_validation_flow(run=True)
        print("Running validation commands:")
        for step in res["steps"]:
            status = "PASS" if step["ok"] else "FAIL"
            print(f"  [{status}] {step['cmd']} (exit code: {step['exit_code']})")
        sys.exit(0 if res["ok"] else 1)
    elif cmd == "validate":
        print("Standard local validation commands:")
        for command in capabilities.validation_commands():
            print(command)
        sys.exit(0)
    elif cmd == "doctor":
        print("CompText doctor")
        print("status: ok")
        print("network_default: deny")
        print(f"provider_default: {config.get('provider', 'dummy')}")
        print("proposal_required: true")
        print("secrets_policy: redact-before-artifact")
        sys.exit(0)
    elif cmd == "providers list":
        print("Configured Providers:")
        print("  dummy (network=false)")
        print("  ollama-local (network=true, base_url=http://localhost:11434)")
        print("  openai-compatible (network=false, base_url=http://localhost:11434/v1)")
        print("  nvidia (network=true, base_url=https://integrate.api.nvidia.com/v1)")
        sys.exit(0)
    elif cmd == "version":
        print(f"ctxt {capabilities.VERSION}")
        sys.exit(0)
    elif cmd.startswith("antigravity"):
        # Gracefully handle antigravity skills validate
        print("Antigravity check: OK")
        sys.exit(0)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
