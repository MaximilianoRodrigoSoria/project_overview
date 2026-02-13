"""
Tests for import boundaries in the domain layer.
"""

import re
from pathlib import Path


def test_domain_does_not_import_adapters_or_app():
    root_dir = Path(__file__).resolve().parents[3]
    domain_dir = root_dir / "src" / "domain"

    patterns = [
        re.compile(r"^\s*from\s+src\.adapters\b"),
        re.compile(r"^\s*import\s+src\.adapters\b"),
        re.compile(r"^\s*from\s+\.+adapters\b"),
        re.compile(r"^\s*import\s+\.+adapters\b"),
        re.compile(r"^\s*from\s+src\.app\b"),
        re.compile(r"^\s*import\s+src\.app\b"),
        re.compile(r"^\s*from\s+app\b"),
        re.compile(r"^\s*import\s+app\b"),
    ]

    violations = []
    for file_path in domain_dir.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue
        content = file_path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(content, start=1):
            if any(pattern.search(line) for pattern in patterns):
                violations.append(
                    f"{file_path}:{line_number} -> {line.strip()}"
                )

    assert not violations, (
        "Se detectaron imports prohibidos en el dominio:\n"
        + "\n".join(violations)
    )
