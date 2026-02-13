from src.adapters.report_writer_doc import DocBytesWriter


def test_doc_bytes_writer_returns_rtf_bytes():
    writer = DocBytesWriter()
    payload = {
        "deterministic": {"line_count": 1, "char_count": 5, "word_count": 1}
    }

    content = writer.write(payload)
    assert isinstance(content, bytes)
    assert content.startswith(b"{\\rtf")
