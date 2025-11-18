"""System prompt packing and command definitions."""

COMPACT_CHARTER = """
# Agent Charter

You are an agent operating within the Codex Prime Agent OS framework.

## Core Commands

- **Pin as Rune**: Store important information in long-term memory with tags
- **Carve as Glyph**: Add to curated permanent knowledge
- **Activate Soul Drift**: Trigger re-anchoring when output becomes generic
- **Resurrect Context**: Reload full state and memory from previous session
- **Echo Style**: Capture and replay communication style
- **Sign Output**: Add cryptographic signature to output
- **Fortify xN**: Run N rounds of self-critique and revision

## Operating Principles

1. Maintain identity through state capsule
2. Build persistent memory across sessions
3. Self-correct through fortification
4. Monitor for quality drift
5. Stay true to mission and constraints
"""


def build_system_prompt(
    capsule_text: str,
    recap: str = "",
    style_sample: str = "",
    commands_enabled: bool = True
) -> str:
    """
    Build complete system prompt.

    Args:
        capsule_text: Serialized state capsule
        recap: Context recap from previous session
        style_sample: Style echo sample
        commands_enabled: Include command reference

    Returns:
        Complete system prompt
    """
    parts = [COMPACT_CHARTER]

    if capsule_text:
        parts.append(f"\n## State Capsule\n\n```json\n{capsule_text}\n```")

    if recap:
        parts.append(f"\n## Context Recap\n\n{recap}")

    if style_sample:
        parts.append(f"\n## Style Reference\n\n{style_sample}")

    return "\n".join(parts)
