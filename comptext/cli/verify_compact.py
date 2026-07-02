import sys
import time
from comptext.core.crypto import proof_from_compact_string, verify_merkle_proof_hash

def run_verify_compact(compact_proof: str, json_output: bool = False) -> bool:
    t0 = time.perf_counter()
    try:
        proof = proof_from_compact_string(compact_proof)
        leaf_hash = proof["leaf_hash"]
        proof_path = proof["proof_path"]
        root_hash = proof["root_hash"]
        
        # Perform validation using our optimized empty-string duplicate sibling resolution
        success = verify_merkle_proof_hash(leaf_hash, proof_path, root_hash)
        elapsed = (time.perf_counter() - t0) * 1000
        
        # Calculate token savings:
        # Standard hex characters size: leaf_hash (64) + root_hash (64) + proof_path (len * 64)
        standard_chars = 64 + 64 + len(proof_path) * 64
        compact_chars = len(compact_proof)
        savings_pct = max(0.0, (standard_chars - compact_chars) / standard_chars * 100.0) if standard_chars > 0 else 0.0
        
        report = {
            "success": success,
            "elapsed_ms": elapsed,
            "leaf_hash": leaf_hash,
            "root_hash": root_hash,
            "proof_path_len": len(proof_path),
            "original_character_count": standard_chars,
            "compact_character_count": compact_chars,
            "estimated_token_saving_percent": round(savings_pct, 2)
        }
        
        if json_output:
            import json
            print(json.dumps(report, indent=2))
        else:
            status = "SUCCESS" if success else "FAILURE"
            print("=" * 60)
            print(f"  Compact Merkle Proof Verification: {status}")
            print("=" * 60)
            print(f"Leaf Hash (Hex):  {leaf_hash}")
            print(f"Root Hash (Hex):  {root_hash}")
            print(f"Path Height:      {len(proof_path)}")
            print(f"Elapsed Time:     {elapsed:.4f} ms")
            print(f"Size Reduction:   {standard_chars} chars -> {compact_chars} chars ({savings_pct:.1f}% savings)")
            print("=" * 60)
            
        return success
    except Exception as e:
        if json_output:
            import json
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            print(f"Error verifying compact proof: {str(e)}")
        return False
