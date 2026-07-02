---
name: verify-compact
description: Verify a compact Base64url Merkle proof string and generate validation/token savings report.
---

# Verify Compact Merkle Proof Skill

Allows agents and developers to verify token-optimized compact Merkle proofs.

## Command Usage
You can run this verification tool directly via the command-line interface:

```bash
python -m comptext.cli verify-compact <compact_proof_string> [--json]
```

## Compact Proof Format
The compact proof string is formatted as:
`leaf_b64url:root_b64url:sibling1_b64url,sibling2_b64url,...`

Where:
- `leaf_b64url` is the leaf digest encoded in URL-safe Base64 without padding.
- `root_b64url` is the root digest encoded in URL-safe Base64 without padding.
- Sibling values are comma-separated URL-safe Base64 digests. Duplicate siblings of odd-level trees are represented by empty strings `""` (resulting in consecutive commas `,` or trailing commas).

## Example
```bash
python -m comptext.cli verify-compact "bGVhZjM:cm9vdF9oYXNo:c2libGluZzE,,c2libGluZzM"
```
