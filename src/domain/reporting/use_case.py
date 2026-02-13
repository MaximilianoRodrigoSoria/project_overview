"""Use cases for reporting domain."""

from typing import Dict, Optional

from .deterministic_analyzer import analyze_text
from .dtos import DeterministicAnalysis, ReportRequest, ReportResult
from ..ports.llm_port import LLMPort


class GenerateReportUseCase:
	"""Generate a report using deterministic analysis and optional narrative."""

	def __init__(self, llm: Optional[LLMPort] = None) -> None:
		self.llm = llm

	def execute(self, request: ReportRequest) -> ReportResult:
		deterministic_raw = analyze_text(request.input_text)
		deterministic = DeterministicAnalysis(**deterministic_raw)

		return ReportResult(
			run_id=request.run_id,
			report_name=request.report_name,
			format=request.format,
			deterministic=deterministic,
			narrative=None
		)

	@staticmethod
	def to_writer_payload(result: ReportResult) -> Dict[str, object]:
		payload = {
			"deterministic": {
				"line_count": result.deterministic.line_count,
				"char_count": result.deterministic.char_count,
				"word_count": result.deterministic.word_count,
				**result.deterministic.metrics,
			}
		}

		if result.narrative:
			payload["narrative"] = {
				"summary": result.narrative.summary,
				"insights": result.narrative.insights,
			}

		return payload

