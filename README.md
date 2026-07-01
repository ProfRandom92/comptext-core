<div align="center">

```
  ██████╗ ██████╗ ███╗   ███╗██████╗ ████████╗███████╗██╗  ██╗████████╗
 ██╔════╝██╔═══██╗████╗ ████║██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝╚══██╔══╝
 ██║     ██║   ██║██╔████╔██║██████╔╝   ██║   █████╗   ╚███╔╝    ██║   
 ██║     ██║   ██║██║╚██╔╝██║██╔═══╝    ██║   ██╔══╝   ██╔██╗    ██║   
 ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║        ██║   ███████╗██╔╝ ██╗   ██║   
  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝        ╚═╝   ╚══════╝╚═╝  ╚═╝   ╚═╝   
```

**THE OPERATING SYSTEM FOR CONTEXT**

[![Python](https://img.shields.io/badge/Python-3.12+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-54%2F54%20passing-brightgreen?style=flat-square)](#testing)
[![Version](https://img.shields.io/badge/Version-v0.1.0-blue?style=flat-square)](https://github.com/ProfRandom92/comptext-core/releases/tag/v0.1.0)
[![Providers](https://img.shields.io/badge/Providers-5%20LLMs-orange?style=flat-square)](#providers)

*Deterministic. Verifiable. Cryptographically signed. Free.*

</div>

---

## What is CompText Core?

**CompText Core** is a unified Python CLI and library that brings together the full CompText ecosystem into a single, coherent tool. It is built around four principles:

- **Deterministic** — identical input always produces identical output, across Python and Rust runtimes (Mulberry32 PRNG, cross-platform verified)
- **Verifiable** — every agent trace is BLAKE3 Merkle-hashed and Ed25519-signed, making replay and drift detection cryptographically provable
- **Cognitive** — built-in Attention-Head Ablation engine to measure how individual transformer attention heads contribute to model behavior
- **Unified** — five LLM providers, FastMCP server, dynamic SKILL.md loading, and a terminal logo renderer — all in one `pip install`

---

## Quick Start

```bash
# Install
git clone https://github.com/ProfRandom92/comptext-core.git
cd comptext-core
pip install -e ".[dev]"

# Run
comptext                          # Displays the ANSI logo
comptext --help                   # All 17 subcommands
comptext audit <path>             # Audit any project directory
comptext audit <path> --json      # Machine-readable output
comptext capabilities --json      # Full capability contract
```

---

## Features

### 🔐 Cryptographic Integrity

```bash
comptext keygen                   # Generate Ed25519 keypair
comptext verify trace.json \      # Verify Merkle + signature
  --pubkey <hex> --signature <hex>
```

Every agent trace is hashed with **BLAKE3** into a Merkle chain and can be signed with **Ed25519**. Tampering with any event in the chain breaks verification instantly.

### 🧠 Cognitive Engine

```python
from comptext.core.cognitive import calculate_delta_ppl

result = calculate_delta_ppl(
    sentence="The cat sat on the mat.",
    layer_index=5,
    head_index=3,
    model_identifier="gpt2"
)
# {'baseline_ppl': 23.4, 'ablated_ppl': 31.7, 'delta_ppl': 8.3, ...}
```

Measures the **perplexity delta** when a specific attention head is ablated (zeroed out) — revealing how much each head contributes to model predictions.

### 📋 Plan Validation

```bash
comptext audit <path> --validate-plan plan.json
```

Compares execution logs against planned contracts to detect **drift, manipulation, or unauthorized deviations** — essential for auditable AI agent pipelines.

### 📦 Dynamic SKILL.md Loader

Place a `SKILL.md` with YAML frontmatter anywhere in your project:

```yaml
---
name: my-skill
version: 1.0.0
mode: deterministic
hash: blake3
---
This skill does X when Y...
```

`CompTextEngine` auto-discovers and merges all `SKILL.md` files in directory order, shaping system behavior dynamically.

### 🖥️ FastMCP Server

```bash
comptext mcp serve
```

Exposes 9 tools over the Model Context Protocol:
`compress`, `sentiment`, `trace_hash`, `sign_trace`, `verify_signature`, `validate_plan`, `calculate_delta_ppl`, `audit`, `hash_text`

---

## Providers

Set API keys in `.env` (copy `.env.example`):

| Provider | Env Var | Notes |
|---|---|---|
| **Anthropic** | `ANTHROPIC_API_KEY` | Claude 3.5/4 family |
| **OpenAI** | `OPENAI_API_KEY` | GPT-4o, o3 |
| **Google** | `GOOGLE_API_KEY` | Gemini 2.5 Pro (google-genai SDK) |
| **xAI** | `XAI_API_KEY` | Grok-3 |
| **NVIDIA NIM** | `NVIDIA_API_KEY` (`nvapi-...`) | 100+ free models |

```bash
comptext chat --provider nvidia   # Free: DeepSeek, Kimi, Llama, GLM, ...
comptext chat --provider anthropic
comptext code "refactor this" --provider openai
```

> **NVIDIA NIM** provides 100+ free serverless models at [build.nvidia.com/models](https://build.nvidia.com/models). Rate-limited — recommended for development, not production.

---

## Architecture

```
comptext-core/
├── comptext/
│   ├── cli/          # audit, verify, logo, code, chat, mcp, keygen
│   ├── core/         # engine, crypto, cognitive, plan_validator,
│   │                 # capabilities, skills
│   ├── mcp/          # FastMCP server (9 tools)
│   ├── providers/    # anthropic, openai, google, xai, nvidia
│   └── terminal/     # ANSI logo renderer + chafa integration
├── assets/
│   └── comptext-logo-braille-color.ans
├── tests/            # 54 tests, 0 warnings
├── SKILL.md          # Root skill definition
├── CHANGELOG.md
└── pyproject.toml
```

---

## Testing

```bash
pytest                            # Run all 54 tests
pytest -m "not slow"              # Skip GPT-2 inference tests
pytest tests/test_crypto.py -v    # Run specific module
```

```
✅ test_capabilities.py     4 tests
✅ test_cognitive.py        2 tests  (GPT-2 attention-head ablation)
✅ test_crypto.py           4 tests  (BLAKE3 Merkle)
✅ test_ed25519_e2e.py      1 test   (full sign+verify flow)
✅ test_engine_stats.py    19 tests  (Mulberry32, sentiment, trace-hash)
┅ test_plan_validator.py   3 tests
✅ test_providers.py       13 tests  (all 5 providers, mocked)
✅ test_renderer.py         6 tests  (logo + chafa fallback)
✅ test_skills_loader.py    3 tests
─────────────────────────────────
   TOTAL                  54/54 ✅
```

---

## Optional: chafa (Terminal Image Rendering)

```bash
# Windows
winget install chafa
scoop install chafa

# macOS
brew install chafa

# Linux
apt install chafa
```

```bash
comptext logo                     # Static ANSI logo (always works)
comptext logo --image myimage.png # Dynamic rendering via chafa
```

chafa is optional — the CLI degrades gracefully to the static ANSI logo if not installed.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full release history.

**v0.1.0** — 2026-07-01 — Initial release

---

## License

MIT © 2026 Alexander Kölnberger — see [LICENSE](LICENSE)

---

<div align="center">

*Built with antigravity. Verified with cryptography. Powered by context.*

</div>
