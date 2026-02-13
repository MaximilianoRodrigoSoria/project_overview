"""
Tests to keep integration tests independent from domain imports.
"""

import re
from pathlib import Path


def test_integration_tests_do_not_import_domain():
    root_dir = Path(__file__).resolve().parents[3]
    integration_dir = root_dir / "tests" / "integration"

    pattern = re.compile(r"^\s*(from|import)\s+src\.domain\b")
    violations = []

    for file_path in integration_dir.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue
        content = file_path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(content, start=1):
            if pattern.search(line):
                violations.append(
                    f"{file_path}:{line_number} -> {line.strip()}"
                )

    assert not violations, (
        "Los tests de integracion no deben importar src.domain:\n"
        + "\n".join(violations)
    )
