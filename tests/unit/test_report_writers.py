"""
Unit tests for report writer adapters.
"""

from src.adapters.report_writer_txt import TextBytesWriter
from src.adapters.report_writer_csv import CSVBytesWriter
from src.adapters.report_writer_markdown import MarkdownBytesWriter


def test_text_writer_returns_bytes():
    writer = TextBytesWriter()
    payload = {
        "deterministic": {"line_count": 2, "char_count": 10, "word_count": 3}
    }

    content = writer.write(payload)
    assert isinstance(content, bytes)
    assert b"line_count" in content


def test_csv_writer_returns_bytes_with_headers():
    writer = CSVBytesWriter()
    payload = {
        "deterministic": {"line_count": 1, "char_count": 5, "word_count": 1}
    }

    content = writer.write(payload)
    assert isinstance(content, bytes)
    assert b"Metric" in content


def test_markdown_writer_returns_bytes():
    writer = MarkdownBytesWriter()
    payload = {
        "deterministic": {"line_count": 1, "char_count": 5, "word_count": 1},
        "narrative": {"summary": "Sample summary", "insights": ["A", "B"]}
    }

    content = writer.write(payload)
    assert isinstance(content, bytes)
    assert b"# Report" in content
