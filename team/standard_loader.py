"""Loads Part 1 of the vendored Agentic GRC Standard so every team
agent's system prompt contains the actual operating principles text,
not a paraphrase of it. Canonical source:
https://github.com/benkanejohns/agentic-grc-standard
Vendored copy here needs updating by hand if the canonical Standard
changes, same tradeoff noted in that repo and the main site.
"""
from pathlib import Path

_STANDARD_PATH = Path(__file__).parent.parent / "standard" / "agentic-grc-standard.md"


def load_part1() -> str:
    text = _STANDARD_PATH.read_text(encoding="utf-8")
    start = text.index("## Part 1")
    end = text.index("## Part 2")
    return text[start:end].strip()


def build_system_prompt(role_instruction: str) -> str:
    return f"{load_part1()}\n\n---\n\n{role_instruction}"
