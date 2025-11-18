"""Tests for drift detection."""

import pytest
from codex_prime.drift import drift_score, is_drifted, generate_reanchor_prompt


def test_drift_score_clean_text():
    """Test drift score on clean, diverse text."""
    text = "The quantum algorithm demonstrates remarkable efficiency in solving complex optimization problems through strategic state manipulation."

    score = drift_score(text)
    assert score < 0.5  # Should be low drift


def test_drift_score_generic_text():
    """Test drift score on generic, repetitive text."""
    text = "As an AI, I cannot provide that information. I apologize, but I don't have access. Let me know if I can help with anything else. Feel free to ask."

    score = drift_score(text)
    assert score > 0.5  # Should be high drift


def test_drift_score_repetitive():
    """Test drift score on repetitive text."""
    text = "The agent agent agent does things things things with the system system system."

    score = drift_score(text)
    assert score > 0.3  # Should show some drift


def test_is_drifted():
    """Test drift detection function."""
    clean = "Implement the binary search algorithm using recursive descent."
    generic = "As an AI, I cannot help. I apologize. Feel free to let me know."

    assert not is_drifted(clean)
    assert is_drifted(generic)


def test_drift_empty_text():
    """Test drift score on empty text."""
    score = drift_score("")
    assert score == 1.0  # Empty should be max drift


def test_generate_reanchor_prompt():
    """Test re-anchoring prompt generation."""
    capsule = '{"persona": "Direct Agent"}'
    user_msg = "Explain Python"

    prompt = generate_reanchor_prompt(capsule, user_msg)

    assert "DRIFT DETECTED" in prompt
    assert "Direct Agent" in prompt
    assert "Explain Python" in prompt
