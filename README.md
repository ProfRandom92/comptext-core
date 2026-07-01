# CompText Forge

Isolated working directory for CompText CLI python integration work.

## LLM Providers
CompText supports multiple LLM providers for query execution and interactive chat:
1. **Google Gemini**: Uses `google-genai` SDK targeting `gemini-2.5-pro`.
2. **xAI**: Targets `grok-3` via standard HTTPX completion endpoints.
3. **OpenAI**: Standard OpenAI SDK compatibility.
4. **Ollama**: Local model deployment and execution.
5. **NVIDIA NIM**: Targets NVIDIA NIM API endpoints using the `openai` SDK.
   - **Endpoint**: `https://integrate.api.nvidia.com/v1`
   - **Authentication**: Requires `NVIDIA_API_KEY` (must start with `nvapi-`).
   - **Model IDs**: Follows `organization/model-name` format (default: `deepseek-ai/deepseek-v4-flash`).
   - **Rate Limits**: The free tier is rate-limited and intended for development only (not production). See [build.nvidia.com/models](https://build.nvidia.com/models) for the full model catalog and documentation. Includes built-in exponential backoff retries.

## Optional Chafa Integration
CompText integrates with `chafa` (a command-line image-to-terminal character renderer) to allow rendering custom images inside the terminal.

### Installation
`chafa` is a system binary, not a Python package. You can install it using your system's package manager:

- **Windows**: `winget install chafa` or `scoop install chafa`
- **macOS**: `brew install chafa`
- **Linux**: `sudo apt install chafa` (Debian/Ubuntu) or `sudo dnf install chafa` (Fedora)

If `chafa` is not installed on your system's `PATH`, the CLI will automatically and gracefully degrade to displaying the static ANSI logo or a plain text title fallback.
