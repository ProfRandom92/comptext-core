import json
import pytest
from pathlib import Path
from comptext.core.crypto import (
    generate_keypair,
    canonical_json,
    merkle_root,
    sign_trace,
    verify_signature,
)

def test_ed25519_e2e_flow():
    # 1. Generate a fresh keypair
    priv_bytes, pub_bytes, priv_hex, pub_hex = generate_keypair()
    assert len(priv_bytes) == 32
    assert len(pub_bytes) == 32

    # 2. Create a sample trace from the events fixture
    fixture_path = Path("tests/fixtures/evidence/hash-chain.events.json")
    assert fixture_path.exists()
    
    with open(fixture_path, "r", encoding="utf-8") as f:
        events = json.load(f)
        
    trace = [canonical_json(event) for event in events]
    assert len(trace) > 0

    # 3. Compute Merkle root and sign it
    root_bytes = merkle_root(trace)
    root_hex = root_bytes.hex()
    
    signature = sign_trace(trace, priv_bytes)
    assert len(signature) == 128  # Ed25519 signature is 64 bytes (128 hex chars)

    # 4. Verify signature succeeds with correct public key
    assert verify_signature(root_hex, signature, pub_bytes) is True

    # 5. Verify signature FAILS with a tampered trace
    tampered_trace = list(trace)
    # Mutate the action of the first event
    tampered_events = json.loads(tampered_trace[0])
    tampered_events["action"] = "tampered_action"
    tampered_trace[0] = canonical_json(tampered_events)
    
    tampered_root_hex = merkle_root(tampered_trace).hex()
    assert verify_signature(tampered_root_hex, signature, pub_bytes) is False

    # 6. Verify signature FAILS with wrong public key
    _, wrong_pub_bytes, _, _ = generate_keypair()
    assert verify_signature(root_hex, signature, wrong_pub_bytes) is False

    # 7. Verify signature FAILS with corrupted signature bytes
    corrupted_sig = signature[:-2] + "00"
    if corrupted_sig == signature:
        corrupted_sig = signature[:-2] + "11"
    assert verify_signature(root_hex, corrupted_sig, pub_bytes) is False
