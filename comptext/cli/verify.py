import sys
import json
import argparse
from pathlib import Path
from comptext.core.crypto import merkle_root, verify_signature, canonical_json

def run_verify(verify_args: list[str], json_output: bool) -> None:
    parser = argparse.ArgumentParser(description="CompText Trace Verification Tool")
    parser.add_argument(
        "trace",
        help="Path to trace JSON file or raw trace string."
    )
    parser.add_argument(
        "--pubkey",
        help="Hex-encoded Ed25519 public key."
    )
    parser.add_argument(
        "--signature",
        help="Hex-encoded Ed25519 signature."
    )

    args = parser.parse_args(verify_args)

    trace_input = args.trace
    pubkey_hex = args.pubkey
    sig_hex = args.signature

    # 1. Resolve trace to list of strings
    trace_list = []
    path = Path(trace_input)
    
    if path.exists() and path.is_file():
        content = path.read_text(encoding="utf-8")
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, (dict, list)):
                        trace_list.append(canonical_json(item))
                    else:
                        trace_list.append(str(item))
            else:
                trace_list = [content]
        except Exception:
            trace_list = [line.strip() for line in content.splitlines() if line.strip()]
    else:
        # Try to parse as inline JSON
        try:
            parsed = json.loads(trace_input)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, (dict, list)):
                        trace_list.append(canonical_json(item))
                    else:
                        trace_list.append(str(item))
            else:
                trace_list = [trace_input]
        except Exception:
            trace_list = [item.strip() for item in trace_input.split(",") if item.strip()]

    if not trace_list:
        if json_output:
            print(json.dumps({"ok": False, "error": "Resolved trace is empty"}, indent=2))
        else:
            print("ERROR: Resolved trace is empty", file=sys.stderr)
        sys.exit(1)

    # 2. Compute Merkle root
    root_bytes = merkle_root(trace_list)
    root_hex = root_bytes.hex()

    # 3. Perform signature verification if requested
    sig_ok = True
    sig_msg = "not_provided"
    
    if pubkey_hex or sig_hex:
        if not (pubkey_hex and sig_hex):
            if json_output:
                print(json.dumps({
                    "ok": False,
                    "error": "Both --pubkey and --signature must be provided for signature verification"
                }, indent=2))
            else:
                print("ERROR: Both --pubkey and --signature must be provided", file=sys.stderr)
            sys.exit(1)
            
        try:
            pubkey_bytes = bytes.fromhex(pubkey_hex)
            sig_ok = verify_signature(root_hex, sig_hex, pubkey_bytes)
            sig_msg = "verified" if sig_ok else "failed"
        except Exception as e:
            sig_ok = False
            sig_msg = f"error: {str(e)}"

    # 4. Return results
    if json_output:
        res = {
            "ok": sig_ok,
            "command": "verify",
            "merkle_root": root_hex,
            "elements_count": len(trace_list),
            "signature_status": sig_msg
        }
        print(json.dumps(res, indent=2))
        sys.exit(0 if sig_ok else 1)
    else:
        print(f"Merkle Root: {root_hex}")
        print(f"Elements:    {len(trace_list)}")
        if pubkey_hex:
            if sig_ok:
                print("SUCCESS: Ed25519 signature verified successfully against Merkle root.")
                sys.exit(0)
            else:
                print(f"ERROR: Ed25519 signature verification failed ({sig_msg}).", file=sys.stderr)
                sys.exit(1)
        else:
            print("Trace integrity checked (no signature provided).")
            sys.exit(0)
