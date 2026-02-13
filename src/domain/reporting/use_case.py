"""Use cases for reporting domain."""

from typing import Dict, Optional

from .deterministic_analyzer import analyze_text
from .dtos import DeterministicAnalysis, NarrativeSection, ReportRequest, ReportResult
from .exceptions import LLMProviderError
from ...ports.llm_port import LLMPort


class GenerateReportUseCase:
	"""Generate a report using deterministic analysis and optional narrative."""

	def __init__(self, llm: Optional[LLMPort] = None) -> None:
		self.llm = llm

	def execute(self, request: ReportRequest) -> ReportResult:
		deterministic_raw = analyze_text(request.input_text)
		deterministic = DeterministicAnalysis(**deterministic_raw)

		narrative = None
		if request.llm_enabled:
			if self.llm is None:
				raise LLMProviderError("LLM provider not configured", run_id=request.run_id)

			prompt = (
				"Provide a short narrative summary for these metrics: "
				f"{deterministic_raw}"
			)
			narrative_text = self.llm.generate_text(prompt)
			narrative = NarrativeSection(summary=narrative_text, insights=[])

		return ReportResult(
			run_id=request.run_id,
			report_name=request.report_name,
			format=request.format,
			deterministic=deterministic,
			narrative=narrative
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

