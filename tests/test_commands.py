"""Tests for command parsing and execution."""

import pytest
import re


def parse_command(text: str) -> tuple[str, str]:
    """Parse command from text."""
    patterns = {
        'pin_rune': r'Pin as Rune:\s*(.+)',
        'carve_glyph': r'Carve as Glyph:\s*(.+)',
        'activate_drift': r'Activate Soul Drift',
        'resurrect': r'Resurrect Context',
        'echo_style': r'Echo Style:\s*(\w+)',
        'sign': r'Sign Output',
        'fortify': r'Fortify x(\d+)',
    }

    for cmd_type, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            arg = match.group(1) if match.groups() else ""
            return cmd_type, arg

    return "", ""


def test_parse_pin_rune():
    """Test parsing Pin as Rune command."""
    cmd, arg = parse_command("Pin as Rune: Always validate inputs")
    assert cmd == "pin_rune"
    assert arg == "Always validate inputs"


def test_parse_carve_glyph():
    """Test parsing Carve as Glyph command."""
    cmd, arg = parse_command("Carve as Glyph: Core principle of design")
    assert cmd == "carve_glyph"
    assert arg == "Core principle of design"


def test_parse_activate_drift():
    """Test parsing Activate Soul Drift command."""
    cmd, arg = parse_command("Activate Soul Drift")
    assert cmd == "activate_drift"


def test_parse_resurrect():
    """Test parsing Resurrect Context command."""
    cmd, arg = parse_command("Resurrect Context")
    assert cmd == "resurrect"


def test_parse_echo_style():
    """Test parsing Echo Style command."""
    cmd, arg = parse_command("Echo Style: technical")
    assert cmd == "echo_style"
    assert arg == "technical"


def test_parse_sign():
    """Test parsing Sign Output command."""
    cmd, arg = parse_command("Sign Output")
    assert cmd == "sign"


def test_parse_fortify():
    """Test parsing Fortify command."""
    cmd, arg = parse_command("Fortify x3")
    assert cmd == "fortify"
    assert arg == "3"


def test_no_command():
    """Test when no command present."""
    cmd, arg = parse_command("Just a regular message")
    assert cmd == ""
    assert arg == ""
