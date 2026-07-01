"""Configuration management for CompText CLI."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR = Path.home() / ".comptext_cli"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config:
    """Manages CompText CLI configuration with environment variable overrides."""

    DEFAULTS = {
        "model": "zai-org/glm-5.1",
        "nvidia_api_key": "",
        "logprobs_enabled": True,
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 4096,
        "mcp_servers": [],
        "skills_dir": "skills",
        "seed": None,
    }

    ENV_MAPPINGS = {
        "nvidia_api_key": ["NVIDIA_API_KEY", "NVAPI_KEY"],
        "model": ["PCOMPTEXT_MODEL"],
        "logprobs_enabled": ["PCOMPTEXT_LOGPROBS"],
    }

    def __init__(self):
        self._config: Dict[str, Any] = self.DEFAULTS.copy()
        self._load_config()
        self._apply_env_overrides()

    def _load_config(self) -> None:
        """Load configuration from file if it exists."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                self._config.update(file_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        for config_key, env_names in self.ENV_MAPPINGS.items():
            for env_name in env_names:
                if env_name in os.environ:
                    value = os.environ[env_name]
                    if config_key == "logprobs_enabled":
                        value = value.lower() in ("true", "1", "yes")
                    self._config[config_key] = value
                    break

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value (in memory only)."""
        self._config[key] = value

    def save(self) -> None:
        """Save configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        return key in self._config