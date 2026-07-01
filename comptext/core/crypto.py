import json
from blake3 import blake3
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

def hash_pair(a: bytes, b: bytes) -> bytes:
    """Hash two digests with BLAKE3, concatenating the lexicographically smaller hash first."""
    if len(a) != 32 or len(b) != 32:
        raise ValueError("Merkle hashes must be exactly 32 bytes.")
    hasher = blake3()
    if a < b:
        hasher.update(a)
        hasher.update(b)
    else:
        hasher.update(b)
        hasher.update(a)
    return hasher.digest()

def sort_json_value(value):
    """Recursively sort dictionary keys for canonical JSON serialization."""
    if isinstance(value, dict):
        return {k: sort_json_value(value[k]) for k in sorted(value.keys())}
    elif isinstance(value, list):
        return [sort_json_value(v) for v in value]
    else:
        return value

def canonical_json(value) -> str:
    """Serialize a JSON value to a canonical string (sorted keys, no spaces)."""
    sorted_val = sort_json_value(value)
    return json.dumps(sorted_val, separators=(',', ':'), ensure_ascii=False)

def verify_ed25519_signature(public_key_hex: str, signature_hex: str, data_bytes: bytes) -> bool:
    """Verify an Ed25519 signature over data_bytes."""
    try:
        pub_bytes = bytes.fromhex(public_key_hex)
        sig_bytes = bytes.fromhex(signature_hex)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        public_key.verify(sig_bytes, data_bytes)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False

def sign_ed25519_data(private_key_hex: str, data_bytes: bytes) -> str:
    """Sign data_bytes using an Ed25519 private key (raw 32-byte seed as hex) and return signature hex."""
    try:
        priv_bytes = bytes.fromhex(private_key_hex)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
        signature = private_key.sign(data_bytes)
        return signature.hex()
    except Exception as e:
        raise ValueError(f"Failed to sign data: {str(e)}")

class MerkleTree:
    """BLAKE3 Merkle tree with sorted pair hashing."""
    def __init__(self, root: bytes, leaves: list[bytes]):
        self.root = root
        self.leaves = leaves

    @classmethod
    def from_leaves(cls, leaves: list[bytes]) -> 'MerkleTree':
        """Build a tree from raw leaf bytes (each leaf is BLAKE3-hashed first)."""
        hashes = [blake3(l).digest() for l in leaves]
        return cls.from_hashes(hashes)

    @classmethod
    def from_hashes(cls, hashes: list[bytes]) -> 'MerkleTree':
        """Build a tree from pre-computed 32-byte leaf digests."""
        if not hashes:
            return cls(b'\x00' * 32, [])
        
        leaves = list(hashes)
        current_level = list(hashes)
        
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                next_level.append(hash_pair(left, right))
            current_level = next_level
            
        return cls(current_level[0], leaves)

    def root_hex(self) -> str:
        return self.root.hex()

    def try_generate_proof(self, index: int) -> dict:
        """Generate a Merkle proof for the leaf at index."""
        if index < 0 or index >= len(self.leaves):
            raise IndexError(f"Merkle proof index out of range: index {index} len {len(self.leaves)}")
            
        proof_path = []
        level = list(self.leaves)
        idx = index
        
        while len(level) > 1:
            sibling_idx = idx + 1 if idx % 2 == 0 else idx - 1
            if sibling_idx < len(level):
                proof_path.append(level[sibling_idx])
            else:
                proof_path.append(level[idx])
                
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left
                next_level.append(hash_pair(left, right))
            level = next_level
            idx //= 2
            
        return {
            "leaf_hash": self.leaves[index].hex(),
            "proof_path": [p.hex() for p in proof_path],
            "root_hash": self.root.hex()
        }

def verify_merkle_proof(leaf: bytes, proof_path_hex: list[str], root_hex: str) -> bool:
    """Verify a proof for a raw leaf (BLAKE3-hashed before tree ascent)."""
    leaf_hash = blake3(leaf).digest()
    return verify_merkle_proof_hash(leaf_hash.hex(), proof_path_hex, root_hex)

def verify_merkle_proof_hash(leaf_hash_hex: str, proof_path_hex: list[str], root_hex: str) -> bool:
    """Verify a proof for a pre-hashed leaf digest."""
    try:
        current = bytes.fromhex(leaf_hash_hex)
        for sibling_hex in proof_path_hex:
            sibling = bytes.fromhex(sibling_hex)
            current = hash_pair(current, sibling)
        return current.hex() == root_hex
    except Exception:
        return False

def generate_keypair() -> tuple[bytes, bytes, str, str]:
    """Generate an Ed25519 private/public keypair.
    Returns:
        (private_key_bytes, public_key_bytes, private_key_hex, public_key_hex)
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    priv_bytes = private_key.private_bytes_raw()
    pub_bytes = public_key.public_bytes_raw()
    
    return priv_bytes, pub_bytes, priv_bytes.hex(), pub_bytes.hex()

def merkle_root(trace: list[str]) -> bytes:
    """Compute the Merkle root of the trace as bytes."""
    leaves = [t.encode("utf-8") for t in trace]
    tree = MerkleTree.from_leaves(leaves)
    return tree.root

def sign_trace(trace: list[str], private_key: bytes) -> str:
    """Compute the Merkle root of the trace, sign it with Ed25519, and return signature hex."""
    root_bytes = merkle_root(trace)
    priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)
    signature = priv_key.sign(root_bytes)
    return signature.hex()

def verify_signature(merkle_root_hex: str, signature: str, public_key: bytes) -> bool:
    """Verify the Ed25519 signature (hex) against the given Merkle root (hex)."""
    try:
        root_bytes = bytes.fromhex(merkle_root_hex)
        sig_bytes = bytes.fromhex(signature)
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
        pub_key.verify(sig_bytes, root_bytes)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False

