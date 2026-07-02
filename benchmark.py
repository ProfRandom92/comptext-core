import time
import statistics
from comptext.core.crypto import MerkleTree, proof_to_compact_string, proof_from_compact_string, verify_merkle_proof_hash

def run_benchmarks():
    sizes = [8, 16, 32, 64, 128]
    print("=" * 70)
    print("  CompText Core Merkle Proof Optimization Benchmark")
    print("=" * 70)
    print(f"{'Leaf Size (N)':<15}{'Std Chars':<12}{'Compact Chars':<15}{'Reduction %':<15}{'Verify Time (ms)':<15}")
    print("-" * 70)
    
    for n in sizes:
        # Generate N leaves
        leaves = [f"leaf_payload_data_item_{i}".encode("utf-8") for i in range(n)]
        tree = MerkleTree.from_leaves(leaves)
        
        std_total_chars = 0
        compact_total_chars = 0
        verify_times = []
        
        # Bench for all leaves in the tree
        for i in range(n):
            proof = tree.try_generate_proof(i)
            compact_str = proof_to_compact_string(proof)
            
            # Count chars
            proof_path_len = len(proof["proof_path"])
            std_chars = 64 + 64 + proof_path_len * 64
            compact_chars = len(compact_str)
            
            std_total_chars += std_chars
            compact_total_chars += compact_chars
            
            # Time validation
            t0 = time.perf_counter()
            recovered = proof_from_compact_string(compact_str)
            verify_merkle_proof_hash(recovered["leaf_hash"], recovered["proof_path"], recovered["root_hash"])
            verify_times.append((time.perf_counter() - t0) * 1000)
            
        avg_std = std_total_chars / n
        avg_compact = compact_total_chars / n
        reduction = (avg_std - avg_compact) / avg_std * 100
        avg_verify = statistics.mean(verify_times)
        
        print(f"{n:<15}{avg_std:<12.1f}{avg_compact:<15.1f}{reduction:<15.2f}{avg_verify:<15.4f}")
    print("=" * 70)

if __name__ == "__main__":
    run_benchmarks()
