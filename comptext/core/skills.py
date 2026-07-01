import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class SkillConfig:
    """Configuration parsed from SKILL.md frontmatter."""
    def __init__(self, name: str = "default", version: str = "0.1", mode: str = "local", hash: str = "blake3", naming: str = "comptext"):
        self.name = name
        self.version = version
        self.mode = mode
        self.hash = hash
        self.naming = naming
        self.guidelines: list[str] = []

    def merge_from_dict(self, data: dict):
        if "name" in data:
            self.name = data["name"]
        if "version" in data:
            self.version = data["version"]
        if "mode" in data:
            self.mode = data["mode"]
        if "hash" in data:
            self.hash = data["hash"]
        if "naming" in data:
            self.naming = data["naming"]

def parse_skill_md(file_path: Path) -> tuple[dict, str]:
    """Parse frontmatter and body from a SKILL.md file."""
    if not file_path.exists():
        return {}, ""
    
    content = file_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}, content
        
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
        
    yaml_text = parts[1]
    body = parts[2]
    
    try:
        data = yaml.safe_load(yaml_text) or {}
    except Exception:
        data = {}
        
    return data, body

def load_skills(root_dir: Path) -> SkillConfig:
    """Load and merge skills configurations from root SKILL.md and skills/*/SKILL.md."""
    config = SkillConfig()
    
    # 1. Load root SKILL.md
    root_skill = root_dir / "SKILL.md"
    if root_skill.exists():
        data, body = parse_skill_md(root_skill)
        config.merge_from_dict(data)
        if body.strip():
            config.guidelines.append(body.strip())
            
    # 2. Load subfolder skills (skills/*/SKILL.md) in directory order
    skills_dir = root_dir / "skills"
    if skills_dir.exists() and skills_dir.is_dir():
        # Get all subdirectories, sort them
        subdirs = sorted([d for d in skills_dir.iterdir() if d.is_dir()])
        for d in subdirs:
            sub_skill = d / "SKILL.md"
            if sub_skill.exists():
                data, body = parse_skill_md(sub_skill)
                config.merge_from_dict(data)
                if body.strip():
                    config.guidelines.append(body.strip())
                    
    return config
