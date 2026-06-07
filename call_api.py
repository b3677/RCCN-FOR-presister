#!/usr/bin/env python3
"""
Call the OpenAI API with a numbered markdown skill and a user task.

Examples:
    python call_api.py --list-skills
    python call_api.py --skill 1 --task "帮我解释 notebooks/set4.ipynb 的分析思路"
    python call_api.py --skill 2 --task-file task.txt --output output/review.md
    python call_api.py --skill 4 --task "总结这个数据集" --output output
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from gpt_tools.run_skill import describe_skills, find_skill_file, read_skill


DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")


def load_task(task: str | None, task_file: str | None) -> str:
    if task and task_file:
        raise ValueError("Use either --task or --task-file, not both.")
    if task_file:
        return Path(task_file).read_text(encoding="utf-8")
    if task:
        return task
    raise ValueError("Please provide --task or --task-file.")


def build_messages(skill_text: str, task_text: str) -> list[dict[str, str]]:
    return [
        {
            "role": "developer",
            "content": (
                "You must follow the skill instructions below when answering.\n\n"
                f"{skill_text}"
            ),
        },
        {"role": "user", "content": task_text},
    ]


def extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    pieces: list[str] = []
    for output_item in getattr(response, "output", []) or []:
        for content_item in getattr(output_item, "content", []) or []:
            text = getattr(content_item, "text", None)
            if text:
                pieces.append(text)
    return "\n".join(pieces).strip()


def call_openai_api(
    skill_text: str,
    task_text: str,
    model: str,
    max_output_tokens: int | None,
) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The openai package is not installed. Install it with: pip install openai"
        ) from exc

    client = OpenAI()
    request: dict[str, Any] = {
        "model": model,
        "input": build_messages(skill_text=skill_text, task_text=task_text),
    }
    if max_output_tokens is not None:
        request["max_output_tokens"] = max_output_tokens

    response = client.responses.create(**request)
    text = extract_output_text(response)
    if not text:
        raise RuntimeError("The API response did not contain output text.")
    return text


def resolve_output_path(output: str, skill_selector: str) -> Path:
    output_path = Path(output)
    if output_path.exists() and output_path.is_dir():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_path / f"skill_{skill_selector}_{timestamp}.md"
    elif output_path.suffix == "":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_path / f"skill_{skill_selector}_{timestamp}.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call the OpenAI API with one numbered skill markdown file."
    )
    parser.add_argument("--list-skills", action="store_true", help="List available skills.")
    parser.add_argument("--skill", help="Skill number, e.g. 1, 01, or SKILL01.")
    parser.add_argument("--task", help="Task description text.")
    parser.add_argument("--task-file", help="Read the task description from a text file.")
    parser.add_argument(
        "--output",
        help="Optional output file path or directory. If omitted, print only.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model name. Defaults to OPENAI_MODEL or {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        help="Optional maximum number of output tokens.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected skill path and task without calling the API.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list_skills:
        print(describe_skills())
        return

    if not args.skill:
        raise ValueError("Please provide --skill, or use --list-skills.")

    skill_path = find_skill_file(args.skill)
    skill_text = read_skill(args.skill)
    task_text = load_task(task=args.task, task_file=args.task_file)

    if args.dry_run:
        print(f"Selected skill: {skill_path}")
        print("\nTask:")
        print(task_text)
        return

    output_text = call_openai_api(
        skill_text=skill_text,
        task_text=task_text,
        model=args.model,
        max_output_tokens=args.max_output_tokens,
    )

    if args.output:
        output_path = resolve_output_path(args.output, skill_selector=str(args.skill))
        output_path.write_text(output_text, encoding="utf-8")
        print(f"Saved output to: {output_path}")
    else:
        print(output_text)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
