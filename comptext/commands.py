"""Command dispatcher for CompText CLI REPL."""

import asyncio
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:
    from .state import AppState


class Command:
    """Represents a CLI command with metadata."""

    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable,
        aliases: Optional[List[str]] = None,
        usage: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.handler = handler
        self.aliases = aliases or []
        self.usage = usage or f"/{name} [arguments]"


class CommandDispatcher:
    """Registers and dispatches CLI commands."""

    def __init__(self, app_state: "AppState"):
        self.app_state = app_state
        self._commands: Dict[str, Command] = {}
        self._register_builtin_commands()

    def _register_builtin_commands(self) -> None:
        """Register all built-in commands."""
        from . import commands as cmd_module

        # Discover and register command functions
        for attr_name in dir(cmd_module):
            if attr_name.startswith("cmd_"):
                command_def = getattr(cmd_module, attr_name)
                if isinstance(command_def, Command):
                    self.register(command_def)

    def register(self, command: Command) -> None:
        """Register a command."""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command

    def dispatch(self, input_line: str) -> Any:
        """Dispatch a command from user input."""
        parts = input_line.strip().split(maxsplit=1)
        if not parts or not parts[0].startswith("/"):
            return None

        cmd_name = parts[0][1:]  # Remove leading "/"
        args = parts[1] if len(parts) > 1 else ""

        command = self._commands.get(cmd_name)
        if not command:
            return f"Unknown command: /{cmd_name}. Use /help for available commands."

        return command.handler(self.app_state, args)

    def list_commands(self) -> List[Command]:
        """List all registered commands."""
        return list(self._commands.values())