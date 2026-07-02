# Implementation Plan: CompText Core Improvements (plan.md)

This plan outlines the implementation steps to achieve the requirements defined in `spec.md`.

---

## 1. Directory Tree & Architecture Mapping

- **Cryptographic Engine**:
  - Modify `comptext/core/crypto.py` to add compact representation, Base64 support, and odd-sibling duplicate optimization.
  - Update `tests/test_crypto.py` to add regression test cases for:
    - Base64 encoding/decoding.
    - Compact proof generation and validation.
    - Odd-level sibling duplicate optimization.

- **LLM Router & Exception Wrapper**:
  - Create `comptext/providers/exceptions.py` to define the unified exception hierarchy:
    - `ProviderError`
    - `ProviderAuthError`
    - `ProviderRateLimitError`
    - `ProviderConnectionError`
    - `ProviderAPIError`
  - Update `comptext/providers/__init__.py` to export these exception classes.
  - Update `comptext/providers/google.py`, `comptext/providers/xai.py`, and `comptext/providers/nvidia.py`:
    - Catch SDK or library exceptions in `complete()` and `chat()`.
    - Map them to the correct standardized exception.
    - Validate API keys in `__init__` and raise `ProviderAuthError` if missing or malformed.
  - Update `tests/test_providers.py` to verify that these wrapper exceptions are correctly thrown when things fail (e.g. rate limits, invalid keys, connection issues).

---

## 2. Plan Verification Loop

We will apply the changes step-by-step.
After each structural modification:
1. Run `pytest -v` locally in the workspace.
2. If any test fails, inspect the trace and fix the issue before proceeding to the next step.
