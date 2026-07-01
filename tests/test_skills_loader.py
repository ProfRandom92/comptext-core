import pytest
from pathlib import Path
from comptext.core.skills import parse_skill_md, load_skills, SkillConfig

def test_parse_skill_md(tmp_path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "---\n"
        "name: test_skill\n"
        "version: 2.1\n"
        "mode: test-mode\n"
        "hash: sha256\n"
        "naming: test-naming\n"
        "---\n"
        "# Guidelines Body\n"
        "Do step 1 and 2.",
        encoding="utf-8"
    )
    
    data, body = parse_skill_md(skill_file)
    assert data["name"] == "test_skill"
    assert data["version"] == 2.1
    assert data["mode"] == "test-mode"
    assert data["hash"] == "sha256"
    assert data["naming"] == "test-naming"
    assert "# Guidelines Body" in body
    assert "Do step 1 and 2." in body

def test_load_skills(tmp_path):
    # 1. Create root SKILL.md
    (tmp_path / "SKILL.md").write_text(
        "---\n"
        "name: root_skill\n"
        "mode: root-mode\n"
        "---\n"
        "Root Guidelines",
        encoding="utf-8"
    )
    
    # 2. Create subfolder skills
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    
    # Skill A
    skill_a_dir = skills_dir / "skill_a"
    skill_a_dir.mkdir()
    (skill_a_dir / "SKILL.md").write_text(
        "---\n"
        "hash: sha512\n"
        "---\n"
        "Skill A Guidelines",
        encoding="utf-8"
    )
    
    # Skill B
    skill_b_dir = skills_dir / "skill_b"
    skill_b_dir.mkdir()
    (skill_b_dir / "SKILL.md").write_text(
        "---\n"
        "naming: custom-naming\n"
        "---\n"
        "Skill B Guidelines",
        encoding="utf-8"
    )
    
    config = load_skills(tmp_path)
    assert config.name == "root_skill"
    assert config.mode == "root-mode"
    assert config.hash == "sha512"
    assert config.naming == "custom-naming"
    
    # Guidelines should be in directory order
    assert len(config.guidelines) == 3
    assert config.guidelines[0] == "Root Guidelines"
    assert config.guidelines[1] == "Skill A Guidelines"
    assert config.guidelines[2] == "Skill B Guidelines"

def test_load_skills_empty_or_missing(tmp_path):
    config = load_skills(tmp_path)
    assert config.name == "default"
    assert config.mode == "local"
    assert len(config.guidelines) == 0
