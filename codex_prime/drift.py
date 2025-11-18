"""Soul Drift Protocol - Detect and correct degraded output quality."""

import re
from typing import Optional
from collections import Counter


# Ban phrases that indicate generic/degraded output
BAN_PHRASES = [
    "as an ai",
    "i cannot",
    "i apologize",
    "i don't have access",
    "let me know if",
    "feel free to",
    "happy to help",
    "is there anything else",
]


def drift_score(text: str, threshold: float = 0.5) -> float:
    """
    Calculate drift score for text.

    Combines multiple heuristics:
    - Ban phrase hit count
    - Type/token ratio (lexical diversity)
    - Repetition score

    Args:
        text: Text to analyze
        threshold: Drift threshold (0-1)

    Returns:
        Drift score between 0 (good) and 1 (drifted)
    """
    if not text:
        return 1.0

    text_lower = text.lower()
    scores = []

    # 1. Ban phrase detection
    ban_hits = sum(1 for phrase in BAN_PHRASES if phrase in text_lower)
    ban_score = min(ban_hits / 3.0, 1.0)  # Normalize to 0-1
    scores.append(ban_score)

    # 2. Type/token ratio (lexical diversity)
    words = re.findall(r'\w+', text_lower)
    if words:
        unique_words = len(set(words))
        total_words = len(words)
        diversity = unique_words / total_words
        diversity_score = 1.0 - diversity  # Lower diversity = higher drift
        scores.append(diversity_score)

    # 3. Repetition score
    if words:
        word_counts = Counter(words)
        # Find most common word frequency (excluding very short words)
        significant_words = [w for w in words if len(w) > 3]
        if significant_words:
            max_repetition = max(Counter(significant_words).values())
            repetition_score = min(max_repetition / 10.0, 1.0)
            scores.append(repetition_score)

    # Average all scores
    final_score = sum(scores) / len(scores) if scores else 0.0
    return final_score


def is_drifted(text: str, threshold: float = 0.5) -> bool:
    """
    Check if text has drifted beyond threshold.

    Args:
        text: Text to check
        threshold: Drift threshold

    Returns:
        True if drifted
    """
    return drift_score(text, threshold) > threshold


def generate_reanchor_prompt(capsule_text: str, original_user_msg: str) -> str:
    """
    Generate re-anchoring prompt to recover from drift.

    Args:
        capsule_text: State capsule JSON
        original_user_msg: Original user message

    Returns:
        Re-anchoring system prompt
    """
    return f"""
SOUL DRIFT DETECTED - REANCHORING

Your previous response showed signs of drift (generic language, low diversity, hedging).

Reconnect to your core identity:

{capsule_text}

Rewrite your response to the user's message with:
1. Direct, specific language
2. Your authentic voice and tone
3. Clear mission alignment
4. No hedging or filler

User message: {original_user_msg}

Provide a rewritten response that embodies your true identity.
"""
