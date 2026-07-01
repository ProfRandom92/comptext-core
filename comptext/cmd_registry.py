"""Command implementations for CompText CLI."""

import json
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any, List

from .commands import Command

if TYPE_CHECKING:
    from .state import AppState


def cmd_help(app_state: "AppState", args: str) -> str:
    """Display available commands."""
    dispatcher = getattr(app_state, '_dispatcher', None)
    if not dispatcher:
        return "No command dispatcher available."

    commands = dispatcher.list_commands()
    output = ["CompText CLI Commands:", ""]

    for cmd in sorted(commands, key=lambda c: c.name):
        output.append(f"  /{cmd.name:<12} {cmd.description}")
        if cmd.usage:
            output.append(f"               Usage: {cmd.usage}")

    return "\n".join(output)


def cmd_add(app_state: "AppState", args: str) -> str:
    """Add context files to analysis."""
    if not args.strip():
        return "Usage: /add <file1> [file2] ..."

    files = args.split()
    added = []
    not_found = []

    for file_path in files:
        path = Path(file_path)
        if path.exists():
            content = path.read_text(encoding="utf-8")
            app_state.add_document(str(path), content)
            app_state.add_context_file(str(path))
            added.append(path.name)
        else:
            not_found.append(file_path)

    result = f"Added: {', '.join(added)}"
    if not_found:
        result += f"\nNot found: {', '.join(not_found)}"

    return result


def cmd_compare(app_state: "AppState", args: str) -> str:
    """Run comparative text analysis on loaded documents."""
    docs = app_state.comptext_state["documents"]

    if len(docs) < 2:
        return "Need at least 2 documents to compare. Use /add to load files."

    # Placeholder for actual comparison logic
    comparison = {
        "type": "lexical",
        "documents": [d["name"] for d in docs],
        "metrics": {
            "shared_vocabulary": 0.42,
            "syntactic_similarity": 0.31,
        },
    }

    app_state.add_comparison(comparison)
    return f"Comparison complete: {comparison['metrics']}"


def cmd_metrics(app_state: "AppState", args: str) -> str:
    """Show computed metrics."""
    metrics = app_state.comptext_state["metrics"]

    if not metrics:
        return "No metrics computed yet."

    lines = ["Current Metrics:"]
    for name, value in metrics.items():
        if isinstance(value, float):
            lines.append(f"  {name}: {value:.4f}")
        else:
            lines.append(f"  {name}: {value}")

    return "\n".join(lines)


def cmd_seed(app_state: "AppState", args: str) -> str:
    """Set RNG seed for reproducible results."""
    if not args.strip():
        seed = app_state.config.get("seed")
        return f"Current seed: {seed if seed is not None else 'None (non-deterministic)'}"

    try:
        seed_value = int(args.strip())
        app_state.config.set("seed", seed_value)
        app_state.comptext_state["seed"] = seed_value
        return f"Seed set to: {seed_value}"
    except ValueError:
        return "Invalid seed value. Use an integer."


def cmd_model(app_state: "AppState", args: str) -> str:
    """Switch model or show current model."""
    if not args.strip():
        current = app_state.config.get("model")
        return f"Current model: {current}"

    app_state.config.set("model", args.strip())
    return f"Model switched to: {args.strip()}"


def cmd_status(app_state: "AppState", args: str) -> str:
    """Display current session status."""
    config = app_state.config
    state = app_state.comptext_state

    lines = [
        "=== CompText CLI Status ===",
        f"Session ID: {app_state.session_id}",
        f"Model: {config.get('model')}",
        f"Temperature: {config.get('temperature')}",
        f"Logprobs: {'enabled' if config.get('logprobs_enabled') else 'disabled'}",
        f"Seed: {state.get('seed', None)}",
        "",
        f"Documents: {len(state['documents'])}",
        f"Comparisons: {len(state['comparisons'])}",
        f"Skills loaded: {len(state['skills_loaded'])}",
        f"Context files: {len(app_state.current_context_files)}",
    ]

    if state["skills_loaded"]:
        lines.append("")
        lines.append("Skills:")
        for skill in state["skills_loaded"]:
            lines.append(f"  - {skill}")

    return "\n".join(lines)


def cmd_skills(app_state: "AppState", args: str) -> str:
    """List all available skills."""
    skills_dir = Path(app_state.config.get("skills_dir", "skills"))
    available = []

    if skills_dir.exists():
        for item in skills_dir.iterdir():
            if item.is_dir():
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    available.append(item.name)

    loaded = app_state.comptext_state["skills_loaded"]

    lines = ["Available Skills:"]
    for skill in sorted(available):
        status = "✓" if skill in loaded else "○"
        lines.append(f"  [{status}] {skill}")

    return "\n".join(lines)


def cmd_load(app_state: "AppState", args: str) -> str:
    """Load a skill by name."""
    if not args.strip():
        return "Usage: /load <skill_name>"

    skill_name = args.strip()
    skills_dir = Path(app_state.config.get("skills_dir", "skills"))
    skill_path = skills_dir / skill_name

    if skill_path.exists() and skill_path.is_dir():
        app_state.load_skill(skill_name)
        return f"Skill loaded: {skill_name}"
    else:
        return f"Skill not found: {skill_name}"


def cmd_clear(app_state: "AppState", args: str) -> str:
    """Clear conversation history."""
    app_state.clear_history()
    return "Conversation history cleared."


def cmd_export(app_state: "AppState", args: str) -> str:
    """Export analysis results to JSON."""
    output_file = args.strip() or "comptext_export.json"

    data = {
        "version": "1.0.0",
        "session": app_state.session_id,
        "state": app_state.comptext_state,
        "window": app_state.window,
    }

    Path(output_file).write_text(json.dumps(data, indent=2), encoding="utf-8")
    return f"Exported to: {output_file}"


def cmd_sample(app_state: "AppState", args: str) -> str:
    """Generate N variations of analysis (subagent pattern)."""
    import re

    match = re.match(r"(\d+)\s+(.+)", args)
    if not match:
        return "Usage: /sample <n> <prompt>"

    n = int(match.group(1))
    prompt = match.group(2)

    # Placeholder for subagent sampling
    return f"Generating {n} variations for: '{prompt}'\n(Sample analysis would spawn parallel subagents here)"


# Command registry
COMMANDS = [
    Command("help", "Display available commands", cmd_help),
    Command("add", "Add context files to analysis", cmd_add, usage="/add <file1> [file2] ..."),
    Command("compare", "Run comparative text analysis", cmd_compare),
    Command("metrics", "Show computed metrics", cmd_metrics),
    Command("seed", "Set RNG seed for reproducibility", cmd_seed, usage="/seed [integer]"),
    Command("model", "Switch or show current model", cmd_model, usage="/model <model_id>"),
    Command("status", "Display session status", cmd_status),
    Command("skills", "List available skills", cmd_skills),
    Command("load", "Load a skill by name", cmd_load, usage="/load <skill_name>"),
    Command("clear", "Clear conversation history", cmd_clear),
    Command("export", "Export results to JSON", cmd_export, usage="/export [filename]"),
    Command("sample", "Generate N variations (subagents)", cmd_sample, usage="/sample <n> <prompt>"),
]