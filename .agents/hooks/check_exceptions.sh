#!/bin/bash
# check_exceptions.sh
# Validation hook for CompText exception standards

python3 -c '
import sys
import json

try:
    data = json.loads(sys.stdin.read())
except Exception as e:
    # If JSON parsing fails, default to allowing the tool
    print(json.dumps({"allow_tool": True}))
    sys.exit(0)

# Extract tool call arguments
args = data.get("toolCall", {}).get("args", {})

def check_value(val):
    if isinstance(val, str):
        # Scan for generic exception raising
        if "raise ValueError" in val or "raise RuntimeError" in val:
            return True
    elif isinstance(val, dict):
        for k, v in val.items():
            if check_value(v):
                return True
    elif isinstance(val, list):
        for item in val:
            if check_value(item):
                return True
    return False

if check_value(args):
    print(json.dumps({
        "allow_tool": False,
        "deny_reason": "Generische ValueError oder RuntimeError sind verboten. Bitte verwende stattdessen die strukturierten Exceptions aus comptext.providers.exceptions."
    }))
else:
    print(json.dumps({"allow_tool": True}))
'
