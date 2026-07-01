import pytest
from comptext.core.crypto import (
    sort_json_value, canonical_json, hash_pair, MerkleTree,
    verify_merkle_proof, verify_merkle_proof_hash,
    verify_ed25519_signature, sign_ed25519_data
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
