import pytest
from comptext.core.crypto import (
    sort_json_value, canonical_json, hash_pair, MerkleTree,
    verify_merkle_proof, verify_merkle_proof_hash,
    verify_ed25519_signature, sign_ed25519_data,
    bytes_to_b64url, b64url_to_bytes,
    proof_to_compact_string, proof_from_compact_string
)
from cryptography.hazmat.primitives.asymmetric import ed25519

def test_canonical_json():
    val = {"b": 2, "a": {"d": 4, "c": 3}, "e": [2, 1]}
    canon = canonical_json(val)
    assert canon == '{"a":{"c":3,"d":4},"b":2,"e":[2,1]}'

def test_hash_pair_commutative():
    h1 = b"\x01" * 32
    h2 = b"\x02" * 32
    p1 = hash_pair(h1, h2)
    p2 = hash_pair(h2, h1)
    assert p1 == p2

def test_merkle_tree():
    leaves = [b"leaf1", b"leaf2", b"leaf3", b"leaf4", b"leaf5"]
    tree = MerkleTree.from_leaves(leaves)
    assert len(tree.leaves) == 5
    
    # Verify all proofs
    for idx, leaf in enumerate(leaves):
        proof = tree.try_generate_proof(idx)
        assert verify_merkle_proof(leaf, proof["proof_path"], tree.root_hex())
        assert verify_merkle_proof_hash(proof["leaf_hash"], proof["proof_path"], tree.root_hex())

def test_ed25519_signatures():
    # Generate temporary key pair
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Get raw bytes
    priv_bytes = private_key.private_bytes_raw()
    pub_bytes = public_key.public_bytes_raw()
    
    data = b"Some secure evidence payload"
    
    # Sign in python
    sig_hex = sign_ed25519_data(priv_bytes.hex(), data)
    
    # Verify in python
    assert verify_ed25519_signature(pub_bytes.hex(), sig_hex, data)
    assert not verify_ed25519_signature(pub_bytes.hex(), sig_hex, data + b" mutated")

def test_base64url_conversion():
    data = b"\x00\x01\x02\xff"
    b64 = bytes_to_b64url(data)
    assert "=" not in b64
    decoded = b64url_to_bytes(b64)
    assert decoded == data

def test_compact_proof_serialization():
    # Test with odd number of leaves to force odd-level duplicate optimization
    leaves = [b"leaf1", b"leaf2", b"leaf3"]
    tree = MerkleTree.from_leaves(leaves)
    
    # Generate proof for index 2 (leaf3)
    # The sibling is duplicated at level 1 because length is odd
    proof = tree.try_generate_proof(2)
    assert "" in proof["proof_path"] # Duplicate should be represented as empty string
    
    # Test standard verification
    assert verify_merkle_proof(b"leaf3", proof["proof_path"], tree.root_hex())
    
    # Test compact serialization
    compact = proof_to_compact_string(proof)
    assert ":" in compact
    
    # Deserialize back
    recovered_proof = proof_from_compact_string(compact)
    assert recovered_proof == proof
    
    # Verify recovered proof
    assert verify_merkle_proof(b"leaf3", recovered_proof["proof_path"], tree.root_hex())
