"""Domain exceptions for reporting."""


from typing import Optional


class ReportingError(Exception):
	"""Base error for reporting domain."""

	error_code = "REPORTING_ERROR"

	def __init__(self, message: str, run_id: Optional[str] = None):
		super().__init__(message)
		self.message = message
		self.run_id = run_id


class ValidationError(ReportingError):
	"""Validation error for request payloads."""

	error_code = "VALIDATION_ERROR"


class InvalidFormatError(ReportingError):
	"""Raised when an unsupported format is requested."""

	error_code = "INVALID_FORMAT"


class LLMProviderError(ReportingError):
	"""Raised when the LLM provider fails."""

	error_code = "LLM_PROVIDER_ERROR"


class ReportGenerationError(ReportingError):
	"""Raised when report generation fails."""

	error_code = "REPORT_GENERATION_ERROR"

