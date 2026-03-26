import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ..app.services.extract import extract_action_items, extract_action_items_llm


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_chat(action_items: list[str]):
    """Return a mock ollama.chat response containing the given action items."""
    import json
    content = json.dumps({"action_items": action_items})
    return SimpleNamespace(message=SimpleNamespace(content=content))


# ---------------------------------------------------------------------------
# extract_action_items_llm tests
# ---------------------------------------------------------------------------

@patch("week2.app.services.extract.chat")
def test_llm_empty_input(mock_chat):
    mock_chat.return_value = _mock_chat([])
    result = extract_action_items_llm("")
    assert result == []


@patch("week2.app.services.extract.chat")
def test_llm_bullet_list(mock_chat):
    mock_chat.return_value = _mock_chat([
        "Set up the database",
        "Implement the API endpoint",
        "Write unit tests",
    ])
    text = """
    - Set up the database
    * Implement the API endpoint
    1. Write unit tests
    """.strip()
    result = extract_action_items_llm(text)
    assert "Set up the database" in result
    assert "Implement the API endpoint" in result
    assert "Write unit tests" in result


@patch("week2.app.services.extract.chat")
def test_llm_keyword_prefixed_lines(mock_chat):
    mock_chat.return_value = _mock_chat([
        "Fix the login bug",
        "Deploy to staging",
        "Review Sarah's PR",
    ])
    text = """
    TODO: Fix the login bug
    Action: Deploy to staging
    Follow-up: Review Sarah's PR
    """.strip()
    result = extract_action_items_llm(text)
    assert "Fix the login bug" in result
    assert "Deploy to staging" in result
    assert "Review Sarah's PR" in result


@patch("week2.app.services.extract.chat")
def test_llm_free_form_notes(mock_chat):
    mock_chat.return_value = _mock_chat([
        "Fix rate limiter bug",
        "Get DB credentials from DevOps",
        "Book a restaurant for team lunch on Friday",
        "Look into upgrading Node version",
    ])
    text = """
    Today: working on rate limiter bug — this is blocking prod deploy!
    Blockers: need DB credentials from DevOps ASAP
    Also: team lunch Friday, someone book a restaurant
    Side note: look into upgrading Node version at some point
    """.strip()
    result = extract_action_items_llm(text)
    assert len(result) == 4


@patch("week2.app.services.extract.chat")
def test_llm_vague_tentative_items_included(mock_chat):
    mock_chat.return_value = _mock_chat([
        "Consider refactoring auth module",
        "Maybe add caching at some point",
    ])
    text = "Consider refactoring the auth module. Maybe add caching at some point."
    result = extract_action_items_llm(text)
    assert len(result) == 2


@patch("week2.app.services.extract.chat")
def test_llm_returns_list_of_strings(mock_chat):
    mock_chat.return_value = _mock_chat(["Do something"])
    result = extract_action_items_llm("Do something")
    assert isinstance(result, list)
    assert all(isinstance(item, str) for item in result)
