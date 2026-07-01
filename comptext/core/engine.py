import math
from typing import Any, Dict, List
from .engine_stats import token_entropy_from_logprobs, compute_sequence_entropy, tokenize, tokens_to_theta

class CompTextEngine:
    """
    CompTextEngine core engine wrapper.
    """
    def __init__(self, config: Dict[str, Any] | None = None):
        from pathlib import Path
        from .skills import load_skills, SkillConfig
        self.config = config or {}
        
        # Load skill config defaults dynamically
        try:
            skill_conf = load_skills(Path("."))
        except Exception:
            skill_conf = SkillConfig()
            
        self.mode = self.config.get("mode", skill_conf.mode)
        self.hash_type = self.config.get("hash", skill_conf.hash)
        # Seed defaults to a fallback or if configured
        self.seed = self.config.get("seed", 42)


    def _compress(self, data: str | List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates Shannon entropy metrics (acting as the core compression representation).
        Supports either raw text string or structured tokens_logprobs list.
        """
        if isinstance(data, str):
            tokens = tokenize(data)
            dim = self.config.get("dim", 8)
            theta = tokens_to_theta(tokens, dim=dim)
            entropy = 0.0
            for p in theta:
                if p > 0.0:
                    entropy -= p * math.log2(p)
            return {
                "type": "text",
                "tokens_count": len(tokens),
                "unique_tokens_count": len(set(tokens)),
                "entropy": round(entropy, 6),
                "theta": theta
            }
        elif isinstance(data, list):
            entropy = compute_sequence_entropy(data)
            return {
                "type": "logprobs",
                "tokens_count": len(data),
                "entropy": round(entropy, 6)
            }
        else:
            raise ValueError("Input data must be a string or a list of token logprobs.")
