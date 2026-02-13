"""DTOs for reporting domain."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .enums import ReportFormat
from .exceptions import InvalidFormatError, ValidationError
from .utils import generate_run_id, validate_run_id


@dataclass
class ReportRequest:
	"""Input payload for report generation."""

	report_name: str
	format: ReportFormat
	input_text: str
	llm_enabled: bool
	run_id: Optional[str] = None
	context: Optional[Dict[str, object]] = None

	def __post_init__(self) -> None:
		if not self.report_name or not self.report_name.strip():
			raise ValidationError("Missing required field: report_name")

		if not self.input_text or not self.input_text.strip():
			raise ValidationError("Missing required field: input_text")

		if not isinstance(self.format, ReportFormat):
			raise InvalidFormatError(
				f"Format not supported: {self.format}"
			)

		if self.run_id:
			validate_run_id(self.run_id)
		else:
			self.run_id = generate_run_id()

		if self.context is None:
			self.context = {}
		
		# Validar que context tenga el campo requerido 'tool'
		if self.context is not None and not isinstance(self.context, dict):
			raise ValidationError("Field 'context' must be an object")
		
		if self.context:
			if 'tool' not in self.context:
				raise ValidationError("Missing required field in context: tool")
			
			# Validar que solo tenga propiedades permitidas (cerrado)
			allowed_keys = {'tool', 'environment'}
			invalid_keys = set(self.context.keys()) - allowed_keys
			if invalid_keys:
				raise ValidationError(
					f"Invalid properties in context: {', '.join(invalid_keys)}. "
					f"Allowed: {', '.join(allowed_keys)}"
				)

	@classmethod
	def from_dict(cls, data: Dict[str, object]) -> "ReportRequest":
		required_fields = ["report_name", "format", "input_text", "llm_enabled", "context"]
		missing = [
			field for field in required_fields
			if field not in data or data[field] in (None, "")
		]

		if missing:
			raise ValidationError(
				f"Missing required field(s): {', '.join(missing)}"
			)

		format_value = str(data.get("format", "")).lower()
		if not ReportFormat.is_valid(format_value):
			raise InvalidFormatError(
				f"Format not supported: {format_value}"
			)

		# Validar context antes de crear la instancia
		context = data.get("context")
		if context is not None:
			if not isinstance(context, dict):
				raise ValidationError("Field 'context' must be an object")
			
			# Validar propiedades permitidas
			allowed_keys = {'tool', 'environment'}
			provided_keys = set(context.keys())
			invalid_keys = provided_keys - allowed_keys
			
			if invalid_keys:
				raise ValidationError(
					f"Invalid properties in context: {', '.join(invalid_keys)}. "
					f"Allowed: {', '.join(allowed_keys)}"
				)

		return cls(
			report_name=str(data["report_name"]),
			format=ReportFormat(format_value),
			input_text=str(data["input_text"]),
			llm_enabled=bool(data["llm_enabled"]),
			run_id=data.get("run_id"),
			context=context or {}
		)


@dataclass
class DeterministicAnalysis:
	"""Deterministic, reproducible metrics for a report."""

	line_count: int
	char_count: int
	word_count: int
	metrics: Dict[str, object] = field(default_factory=dict)

	def __post_init__(self) -> None:
		for field_name, value in (
			("line_count", self.line_count),
			("char_count", self.char_count),
			("word_count", self.word_count),
		):
			if value < 0:
				raise ValidationError(
					f"{field_name} must be non-negative"
				)


@dataclass
class NarrativeSection:
	"""Optional narrative output."""

	summary: str
	insights: List[str] = field(default_factory=list)


@dataclass
class ReportResult:
	"""Final report payload before rendering."""

	run_id: str
	report_name: str
	format: ReportFormat
	deterministic: DeterministicAnalysis
	narrative: Optional[NarrativeSection] = None
	generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

