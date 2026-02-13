"""Deterministic analysis helpers for reporting."""

from typing import Dict


def analyze_text(input_text: str) -> Dict[str, int]:
    """Analyze text deterministically."""
    lines = input_text.splitlines()
    words = input_text.split()

    return {
        "line_count": len(lines),
        "char_count": len(input_text),
        "word_count": len(words),
    }
