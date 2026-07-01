"""
Central application state management for CompText CLI.

Manages conversation history, loaded context, skills, and MCP tools.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config


class AppState:
    """Central state management for CompText CLI sessions."""

    def __init__(self):
        self.config = Config()

        # Conversation state
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_context_files: List[str] = []

        # Analysis state
        self.comptext_state: Dict[str, Any] = {
            "documents": [],
            "comparisons": [],
            "metrics": {},
            "skills_loaded": [],
            "mcp_tools_available": [],
            "seed": self.config.get("seed"),
        }

        # Session state
        self.session_id: str = f"sess_{os.getpid()}_{id(self)}"
        self.started_at: float = __import__('time').time()

    @property
    def window(self) -> Dict[str, Any]:
        """
        Return a compact snapshot of current state for prompt injection.
        Similar to CompText v2's ManagerAgent global state.
        """
        return {
            "CompTextState": self.comptext_state,
            "conversation_turns": len(self.conversation_history),
            "context_files": len(self.current_context_files),
            "session_id": self.session_id,
        }

    def add_document(self, path: str, content: str) -> None:
        """Add a document to the analysis state."""
        doc_id = f"doc_{len(self.comptext_state['documents']) + 1}"
        self.comptext_state["documents"].append({
            "id": doc_id,
            "path": path,
            "name": Path(path).name,
            "size": len(content),
        })

    def add_comparison(self, comparison: Dict[str, Any]) -> None:
        """Add a comparative analysis result."""
        self.comptext_state["comparisons"].append(comparison)

    def add_metric(self, name: str, value: Any) -> None:
        """Add a computed metric."""
        self.comptext_state["metrics"][name] = value

    def load_skill(self, skill_name: str) -> None:
        """Record a loaded skill."""
        if skill_name not in self.comptext_state["skills_loaded"]:
            self.comptext_state["skills_loaded"].append(skill_name)

    def add_context_file(self, path: str) -> None:
        """Add a context file to the current session."""
        if path not in self.current_context_files:
            self.current_context_files.append(path)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
        self.comptext_state["comparisons"].clear()

    def __repr__(self) -> str:
        return (
            f"AppState(session={self.session_id}, "
            f"docs={len(self.comptext_state['documents'])}, "
            f"comparisons={len(self.comptext_state['comparisons'])}, "
            f"skills={len(self.comptext_state['skills_loaded'])})"
        )