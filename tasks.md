# Tasks Breakdown: CompText Core Improvements (tasks.md)

This task list defines the step-by-step implementation and verification tasks.

---

## 1. Exception Unification Tasks

- [x] **Task 1**: Create `comptext/providers/exceptions.py` with standard `ProviderError` exceptions hierarchy.
- [x] **Task 2**: Update `comptext/providers/__init__.py` to import/export standard exception types.
- [x] **Task 3**: Refactor `comptext/providers/nvidia.py` to check keys on init and wrap internal OpenAI exceptions in `ProviderError` variants.
- [x] **Task 4**: Refactor `comptext/providers/google.py` to check keys on init and wrap internal Google API exceptions.
- [x] **Task 5**: Refactor `comptext/providers/xai.py` to check keys on init and wrap HTTPX exceptions.
- [x] **Task 6**: Run `pytest -v` to check for syntax and regression errors.
- [x] **Task 7**: Add/update tests in `tests/test_providers.py` to cover the new exception classes. Run `pytest -v` and verify.

---

## 2. Cryptographic Merkle Proof Optimization Tasks

- [x] **Task 8**: Implement Base64 and compact proof helpers in `comptext/core/crypto.py`. Update `MerkleTree.try_generate_proof` to support empty-string duplicate sibling placeholders.
- [x] **Task 9**: Update `tests/test_crypto.py` to add unit tests verifying Base64 conversion, compact serialization/deserialization, and duplicate sibling omission.
- [x] **Task 10**: Run final full test suite `pytest -v` and verify that all tests pass without errors.
