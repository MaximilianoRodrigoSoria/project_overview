"""Factory for report writers."""

from typing import Dict, Type

from ..domain.reporting.enums import ReportFormat
from .report_writer_csv import CSVBytesWriter
from .report_writer_txt import TextBytesWriter
from .report_writer_markdown import MarkdownBytesWriter
from .report_writer_excel import ExcelBytesWriter
from .report_writer_doc import DocBytesWriter


_WRITERS: Dict[ReportFormat, Type] = {
    ReportFormat.CSV: CSVBytesWriter,
    ReportFormat.TXT: TextBytesWriter,
    ReportFormat.MARKDOWN: MarkdownBytesWriter,
    ReportFormat.EXCEL: ExcelBytesWriter,
    ReportFormat.DOC: DocBytesWriter,
}


def get_writer(report_format: ReportFormat):
    writer_cls = _WRITERS.get(report_format)
    if writer_cls is None:
        raise ValueError(f"Unsupported format: {report_format}")
    return writer_cls()
