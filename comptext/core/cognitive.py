import copy
import math
import time
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

_ENGINE_CACHE = {}

class AblationEngine:
    """Engine performing in-place Attention-Head Ablation on GPT-2 style models."""
    def __init__(self, model_name: str = "gpt2"):
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
        self.device = torch.device(device)
        self.model_name = model_name

        self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        self.model = GPT2LMHeadModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

        cfg = self.model.config
        self.num_layers = cfg.n_layer
        self.num_heads  = cfg.n_head
        self.embed_dim  = cfg.n_embd
        self.head_dim   = self.embed_dim // self.num_heads

    def calculate_perplexity(self, text: str) -> float:
        """Calculate perplexity of text (exp of cross-entropy loss)."""
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss
            perplexity = math.exp(loss.item())
        return perplexity

    def _ablate_head_inplace(self, layer_idx: int, head_idx: int) -> None:
        """Zero out the Q, K, and V weight slices for the specified head in-place."""
        if layer_idx < 0 or layer_idx >= self.num_layers:
            raise ValueError(f"layer_index {layer_idx} out of range (0-{self.num_layers-1})")
        if head_idx < 0 or head_idx >= self.num_heads:
            raise ValueError(f"head_index {head_idx} out of range (0-{self.num_heads-1})")
            
        attn = self.model.transformer.h[layer_idx].attn
        s = head_idx * self.head_dim
        e = s + self.head_dim

        with torch.no_grad():
            # Slice Q, K, V segments and set to 0
            attn.c_attn.weight[:, s:e] = 0.0
            attn.c_attn.weight[:, self.embed_dim + s : self.embed_dim + e] = 0.0
            attn.c_attn.weight[:, 2 * self.embed_dim + s : 2 * self.embed_dim + e] = 0.0

    def run_iit_audit(self, text: str, layer_idx: int, head_idx: int, verbose: bool = True) -> dict:
        """Run IIT audit by comparing perplexity before and after head ablation."""
        t0 = time.perf_counter()
        
        # Validations
        if layer_idx < 0 or layer_idx >= self.num_layers:
            raise ValueError(f"layer_index {layer_idx} out of range (0-{self.num_layers-1})")
        if head_idx < 0 or head_idx >= self.num_heads:
            raise ValueError(f"head_index {head_idx} out of range (0-{self.num_heads-1})")
            
        baseline_ppl = self.calculate_perplexity(text)
        
        # Save snapshot
        original_weights = copy.deepcopy(
            self.model.transformer.h[layer_idx].attn.c_attn.weight.data
        )
        
        # Inplace ablation
        self._ablate_head_inplace(layer_idx, head_idx)
        ablated_ppl = self.calculate_perplexity(text)
        
        # Restore weights
        with torch.no_grad():
            self.model.transformer.h[layer_idx].attn.c_attn.weight.data.copy_(
                original_weights
            )
            
        delta_ppl = ablated_ppl - baseline_ppl
        elapsed_ms = (time.perf_counter() - t0) * 1000
        
        # Interpret classifications
        if delta_ppl < 1.5:
            classification = "REDUNDANT"
        elif delta_ppl < 10.0:
            classification = "PARTIAL"
        elif delta_ppl < 15.0:
            classification = "CAUSAL"
        else:
            classification = "ESSENTIAL"
            
        return {
            "baseline_ppl": baseline_ppl,
            "ablated_ppl": ablated_ppl,
            "delta_ppl": delta_ppl,
            "classification": classification,
            "elapsed_ms": elapsed_ms,
            "layer_index": layer_idx,
            "head_index": head_idx,
            "model_identifier": self.model_name
        }

def calculate_delta_ppl(
    sentence: str,
    layer_index: int,
    head_index: int,
    model_identifier: str = "gpt2",
    verbose: bool = True
) -> dict:
    """Perform Attention-Head Ablation and calculate delta perplexity."""
    if model_identifier not in _ENGINE_CACHE:
        _ENGINE_CACHE[model_identifier] = AblationEngine(model_name=model_identifier)
        
    engine = _ENGINE_CACHE[model_identifier]
    return engine.run_iit_audit(
        text=sentence,
        layer_idx=layer_index,
        head_idx=head_index,
        verbose=verbose
    )
