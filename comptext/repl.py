"""REPL engine for interactive CompText CLI with live streaming support."""

import asyncio
from typing import TYPE_CHECKING, List, Optional
from pathlib import Path

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.styles import Style
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

if TYPE_CHECKING:
    from .state import AppState
    from .commands import CommandDispatcher


class CompTextREPL:
    """Interactive REPL with live streaming and entropy analysis."""

    STYLE = Style.from_dict({
        "prompt": "ansicyan bold",
        "continuation": "ansigray",
        "command": "ansimagenta bold",
        "error": "ansired bold",
    })

    def __init__(self, app_state: "AppState"):
        self.app_state = app_state
        self._dispatcher: Optional["CommandDispatcher"] = None
        self._running = False

        if PROMPT_TOOLKIT_AVAILABLE:
            history_file = Path.home() / ".comptext" / "cli_history"
            self._session = PromptSession(
                history=FileHistory(str(history_file)),
                auto_suggest=AutoSuggestFromHistory(),
                style=self.STYLE,
            )
        else:
            self._session = None

    def setup_dispatcher(self, dispatcher: "CommandDispatcher") -> None:
        """Set up the command dispatcher."""
        self._dispatcher = dispatcher
        self.app_state._dispatcher = dispatcher

    async def prompt(self, message: str = "comp> ") -> str:
        """Get user input with optional live streaming."""
        if self._session:
            return await self._session.prompt_async(message)
        else:
            try:
                return input(message)
            except EOFError:
                return "/quit"

    async def run(self) -> None:
        """Main REPL loop."""
        self._running = True

        print("\n" + "=" * 50)
        print("  CompText CLI v1.0.0 - Comparative Text Analysis")
        print("  Type /help for available commands")
        print("=" * 50 + "\n")

        while self._running:
            try:
                user_input = await self.prompt()
                response = await self._handle_input(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\nUse /quit to exit")
                continue
            except Exception as e:
                print(f"Error: {e}")

    async def _handle_input(self, user_input: str) -> str:
        """Process user input and return response."""
        if not user_input.strip():
            return ""

        # Check for commands
        if user_input.strip().startswith("/"):
            if not self._dispatcher:
                return "Error: Command dispatcher not initialized."
            return self._dispatcher.dispatch(user_input)

        # Free text - invoke NVIDIA client for analysis
        return await self._chat_with_nvidia(user_input)

    async def _chat_with_nvidia(self, user_input: str) -> str:
        """Send free text to NVIDIA NIM for analysis."""
        from .nvidia_client import NVIDIAClient

        config = self.app_state.config
        api_key = config.get("nvidia_api_key")

        if not api_key:
            return "Error: NVIDIA API key not set. Use /key <api_key> first."

        # Build messages from history
        messages: List[dict] = []

        # Add system context
        system_prompt = self._build_system_prompt()
        messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        for msg in self.app_state.conversation_history[-10:]:
            messages.append(msg)

        # Add current user message
        messages.append({"role": "user", "content": user_input})

        # Store for context
        self.app_state.conversation_history.append(
            {"role": "user", "content": user_input}
        )

        # Create client and stream response
        client = NVIDIAClient(
            api_key=api_key,
            model=config.get("model"),
            temperature=config.get("temperature"),
            top_p=config.get("top_p"),
            logprobs=config.get("logprobs_enabled"),
        )

        full_response = ""
        print("CompText: ", end="", flush=True)

        try:
            async for chunk in client.chat(messages, stream=True):
                if "choices" in chunk and chunk["choices"]:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        content = delta["content"]
                        full_response += content
                        print(content, end="", flush=True)

            print()  # Newline after streaming

            # Store assistant response
            self.app_state.conversation_history.append(
                {"role": "assistant", "content": full_response}
            )

        finally:
            await client.close()

        return full_response

    def _build_system_prompt(self) -> str:
        """Build system prompt with context."""
        window = self.app_state.window
        return f"""You are CompText, an AI assistant for comparative text analysis.

Current Session State:
{window}

You specialize in:
- Probabilistic text analysis
- Comparative document analysis
- Bayesian uncertainty quantification
- Multi-agent collaborative reasoning

Provide concise, analytical responses. Use /help for available commands."""

    def stop(self) -> None:
        """Stop the REPL."""
        self._running = False


def run_cli() -> None:
    """Entry point for CLI execution."""
    import sys
    if len(sys.argv) > 1:
        from .cli.__main__ import main as cli_main
        cli_main()
        return

    from .state import AppState
    from .commands import CommandDispatcher, COMMANDS

    app_state = AppState()
    dispatcher = CommandDispatcher(app_state)

    # Register all commands
    for cmd in COMMANDS:
        dispatcher.register(cmd)

    repl = CompTextREPL(app_state)
    repl.setup_dispatcher(dispatcher)

    from .terminal.renderer import render_logo
    render_logo()

    asyncio.run(repl.run())



if __name__ == "__main__":
    run_cli()