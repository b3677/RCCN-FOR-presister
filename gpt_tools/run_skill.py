#!/usr/bin/env python3
"""
Read numbered skill markdown files from gpt_tools/skills.

Examples:
    python gpt_tools/run_skill.py --list
    python gpt_tools/run_skill.py 1
    python gpt_tools/run_skill.py SKILL04
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


SKILLS_DIR = Path(__file__).resolve().parent / "skills"


@dataclass(frozen=True)
class SkillInfo:
    number: int | None
    path: Path

    @property
    def label(self) -> str:
        if self.number is None:
            return self.path.stem
        return f"SKILL{self.number:02d}"


def _skill_number_from_name(name: str) -> int | None:
    match = re.search(r"skill[-_ ]*0*(\d+)", name, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def list_skills(skills_dir: Path = SKILLS_DIR) -> list[SkillInfo]:
    skills = [
        SkillInfo(number=_skill_number_from_name(path.stem), path=path)
        for path in skills_dir.glob("*.md")
    ]
    return sorted(
        skills,
        key=lambda item: (
            item.number is None,
            item.number if item.number is not None else 10**9,
            item.path.name.lower(),
        ),
    )


def find_skill_file(selector: str | int, skills_dir: Path = SKILLS_DIR) -> Path:
    selector_text = str(selector).strip()
    if not selector_text:
        raise ValueError("Skill selector cannot be empty.")

    skills = list_skills(skills_dir)
    selector_number = _skill_number_from_name(selector_text)
    if selector_text.isdigit():
        selector_number = int(selector_text)

    if selector_number is not None:
        matches = [skill for skill in skills if skill.number == selector_number]
        if matches:
            return matches[0].path
        raise FileNotFoundError(f"No markdown skill found for number {selector_number}.")

    direct_path = skills_dir / selector_text
    if direct_path.suffix.lower() != ".md":
        direct_path = direct_path.with_suffix(".md")
    if direct_path.exists():
        return direct_path

    lowered = selector_text.lower()
    matches = [
        skill.path
        for skill in skills
        if lowered in skill.path.stem.lower() or lowered == skill.label.lower()
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise ValueError(f"Selector {selector_text!r} matched multiple skills: {names}")

    available = ", ".join(f"{skill.label}: {skill.path.name}" for skill in skills)
    raise FileNotFoundError(
        f"No skill matched {selector_text!r}. Available skills: {available}"
    )


def read_skill(selector: str | int, skills_dir: Path = SKILLS_DIR) -> str:
    skill_path = find_skill_file(selector, skills_dir=skills_dir)
    return skill_path.read_text(encoding="utf-8")


def describe_skills(skills_dir: Path = SKILLS_DIR) -> str:
    rows = [
        f"{skill.label}\t{skill.path.name}"
        for skill in list_skills(skills_dir=skills_dir)
    ]
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Read a numbered markdown skill.")
    parser.add_argument("skill", nargs="?", help="Skill number, e.g. 1 or SKILL01.")
    parser.add_argument("--list", action="store_true", help="List available skills.")
    args = parser.parse_args()

    if args.list:
        print(describe_skills())
        return

    if not args.skill:
        parser.error("Please provide a skill number, or use --list.")

    print(read_skill(args.skill))


if __name__ == "__main__":
    main()
