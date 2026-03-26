from __future__ import annotations

import re
from typing import List

from ollama import chat
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


class _ActionItems(BaseModel):
    action_items: list[str]


def extract_action_items_llm(text: str, model: str = "mistral:7b") -> List[str]:
    """Extract action items from text using an Ollama LLM with structured output."""
    response = chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an assistant that extracts action items from notes. "
                    "Return ALL tasks, to-dos, follow-ups, and suggestions found in the text — "
                    "including vague, tentative, or low-priority ones like 'look into X' or 'at some point'. "
                    "Do NOT filter out anything. Respond with a JSON object containing an 'action_items' key with an array of strings."
                ),
            },
            {
                "role": "user",
                "content": f"Extract all action items from the following note:\n\n{text}",
            },
        ],
        format=_ActionItems.model_json_schema(),
        options={"temperature": 0, "num_ctx": 512, "num_predict": 256},
    )
    result = _ActionItems.model_validate_json(response.message.content)
    return result.action_items


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters
