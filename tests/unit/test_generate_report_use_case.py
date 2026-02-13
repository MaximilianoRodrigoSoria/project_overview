from src.domain.reporting.dtos import ReportRequest
from src.domain.reporting.enums import ReportFormat
from src.domain.reporting.use_case import GenerateReportUseCase


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def generate_text(self, prompt: str, system_prompt: str = None) -> str:
        self.calls += 1
        return "Narrative summary"


def test_generate_report_with_llm_disabled_returns_deterministic_only():
    use_case = GenerateReportUseCase(llm=FakeLLM())
    request = ReportRequest(
        report_name="report",
        format=ReportFormat.TXT,
        input_text="one two\nthree",
        llm_enabled=False,
        run_id="run-1"
    )

    result = use_case.execute(request)

    assert result.narrative is None
    assert result.deterministic.line_count == 2
    assert result.deterministic.word_count == 3


def test_generate_report_with_llm_enabled_adds_narrative():
    llm = FakeLLM()
    use_case = GenerateReportUseCase(llm=llm)
    request = ReportRequest(
        report_name="report",
        format=ReportFormat.TXT,
        input_text="one two\nthree",
        llm_enabled=True,
        run_id="run-2"
    )

    result = use_case.execute(request)

    assert llm.calls == 1
    assert result.narrative is not None
    assert result.narrative.summary == "Narrative summary"
    assert result.deterministic.line_count == 2
