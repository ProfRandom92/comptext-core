import pytest
from comptext.core.cognitive import calculate_delta_ppl

@pytest.mark.slow
def test_calculate_delta_ppl_e2e():
    sentence = "The cat sat on the mat."
    # Use gpt2 (smallest variant)
    result = calculate_delta_ppl(
        sentence=sentence,
        layer_index=0,
        head_index=0,
        model_identifier="gpt2",
        verbose=False
    )
    
    assert isinstance(result, dict)
    assert "baseline_ppl" in result
    assert "ablated_ppl" in result
    assert "delta_ppl" in result
    
    baseline = result["baseline_ppl"]
    ablated = result["ablated_ppl"]
    delta = result["delta_ppl"]
    
    # Verify positive floats
    assert isinstance(baseline, float) and baseline > 0
    assert isinstance(ablated, float) and ablated > 0
    
    # Verify delta calculation
    assert abs(delta - (ablated - baseline)) < 1e-6
    assert result["layer_index"] == 0
    assert result["head_index"] == 0
    assert result["model_identifier"] == "gpt2"

@pytest.mark.slow
def test_calculate_delta_ppl_invalid_indices():
    # Out of range indices should raise ValueError
    with pytest.raises(ValueError) as exc:
        calculate_delta_ppl(
            sentence="Hello world.",
            layer_index=99,  # GPT-2 has 12 layers (0-11)
            head_index=0,
            model_identifier="gpt2",
            verbose=False
        )
    assert "out of range" in str(exc.value)

    with pytest.raises(ValueError) as exc2:
        calculate_delta_ppl(
            sentence="Hello world.",
            layer_index=0,
            head_index=99,  # GPT-2 has 12 heads (0-11)
            model_identifier="gpt2",
            verbose=False
        )
    assert "out of range" in str(exc2.value)
