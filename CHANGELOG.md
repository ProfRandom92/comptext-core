# Changelog

## [Unreleased]
### Added
- Community-ready README.md with badges, Mermaid architecture/sequence diagrams, and demo GIF.
- Detailed Ollama integration and chafa installation guide.
- Added regression tests for REPL session termination and non-streaming NVIDIA client generator.

### Fixed
- Fixed REPL interactive session termination via `/quit` or `/exit` commands.
- Corrected `COMMANDS` import source mapping in CLI launcher execution.
- Fixed NVIDIA client generator compatibility with Python 3.12+ and non-streaming flow termination.

## [0.1.0] — 2026-07-01
### Added
- Deterministic CompText engine (Mulberry32, cross-runtime Python/Rust parity)
- BLAKE3 Merkle tree hashing + Ed25519 signing/verification
- Attention-Head Ablation cognitive engine (GPT-2, calculate_delta_ppl)
- Plan validation (execution log vs. contract drift detection)
- 6 providers: Anthropic, OpenAI, Google (genai), xAI/Grok, NVIDIA NIM, Ollama
- Dynamic SKILL.md loader (frontmatter-driven config)
- FastMCP server (9 exposed tools)
- Terminal logo renderer (chafa + static ANSI fallback)
- comptext audit, verify, keygen, chat, code, logo, mcp, capabilities
- 57/57 tests passing
