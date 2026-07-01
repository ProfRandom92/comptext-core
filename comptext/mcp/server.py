from mcp.server.fastmcp import FastMCP
from ..core.engine import CompTextEngine
from ..core.engine_stats import compute_sentiment_distribution, compute_trace_hash as _compute_trace_hash

mcp = FastMCP("comptext-validation-server")

@mcp.tool()
def compress(text: str) -> dict:
    """
    Compress the input text into a probabilistic token representation
    and calculate Shannon entropy.
    """
    engine = CompTextEngine()
    return engine._compress(text)

@mcp.tool()
def analyze_sentiment(text: str) -> dict:
    """
    Compute the smoothed empirical probability distribution over the sentiment lexicon for the given text.
    """
    return compute_sentiment_distribution(text)

@mcp.tool()
def compute_trace_hash(trace: list[str]) -> str:
    """
    Compute the cryptographic BLAKE3 replay integrity hash of agent traces.
    """
    return _compute_trace_hash(trace)

@mcp.tool()
def sign_trace(trace: list[str], private_key_hex: str) -> dict:
    """Sign an execution trace using an Ed25519 private key (hex) and return signature hex."""
    from ..core.crypto import sign_trace as _sign_trace
    try:
        priv_bytes = bytes.fromhex(private_key_hex)
        sig = _sign_trace(trace, priv_bytes)
        return {"ok": True, "signature": sig}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@mcp.tool()
def verify_signature(merkle_root: str, signature: str, public_key_hex: str) -> dict:
    """Verify an Ed25519 signature (hex) against a Merkle root (hex) using a public key (hex)."""
    from ..core.crypto import verify_signature as _verify_signature
    try:
        pub_bytes = bytes.fromhex(public_key_hex)
        ok = _verify_signature(merkle_root, signature, pub_bytes)
        return {"ok": ok, "signature_status": "verified" if ok else "failed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@mcp.tool()
def validate_plan(execution_log_path: str, plan_path: str) -> dict:
    """Validate an execution log file against a plan file using plan_validator."""
    from ..core.plan_validator import validate_replay_contract
    import json
    try:
        with open(execution_log_path, "r", encoding="utf-8") as f:
            log_data = json.load(f)
        with open(plan_path, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
        
        errors = validate_replay_contract(log_data, plan_data)
        return {
            "ok": len(errors) == 0,
            "errors": errors
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

@mcp.tool()
def calculate_delta_ppl(
    sentence: str,
    layer_index: int,
    head_index: int,
    model_identifier: str = "gpt2",
    verbose: bool = True
) -> dict:
    """Führt eine gezielte Attention-Head-Ablation durch, um die Delta-Perplexität und Kausalstruktur eines Zielmodells zu berechnen."""
    from ..core.cognitive import calculate_delta_ppl as _calculate_delta_ppl
    return _calculate_delta_ppl(
        sentence=sentence,
        layer_index=layer_index,
        head_index=head_index,
        model_identifier=model_identifier,
        verbose=verbose
    )



if __name__ == "__main__":
    mcp.run(transport="stdio")
