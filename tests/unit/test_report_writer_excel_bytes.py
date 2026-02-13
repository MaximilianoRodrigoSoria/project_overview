from src.adapters.report_writer_excel import ExcelBytesWriter


def test_excel_bytes_writer_returns_bytes():
    writer = ExcelBytesWriter()
    payload = {
        "deterministic": {"line_count": 1, "char_count": 5, "word_count": 1}
    }

    content = writer.write(payload)
    assert isinstance(content, bytes)
    assert len(content) > 0
