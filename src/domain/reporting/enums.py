"""Enums for reporting domain."""

from enum import Enum


class ReportFormat(str, Enum):
	"""Supported report output formats."""

	EXCEL = "excel"
	CSV = "csv"
	TXT = "txt"
	MARKDOWN = "markdown"
	DOC = "doc"

	@classmethod
	def is_valid(cls, value: str) -> bool:
		if not value:
			return False
		try:
			cls(value.lower())
			return True
		except ValueError:
			return False

	@classmethod
	def values(cls) -> list:
		return [fmt.value for fmt in cls]

