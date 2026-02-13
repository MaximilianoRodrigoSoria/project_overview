from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from typing import Dict

from src.domain.use_cases import GenerateReportUseCase
from src.ports.cache_port import CachePort
from src.config.settings import settings


class FakeLogReader:
    def read_log(self, source: str) -> str:
        return "log"


class FakeAnalyzer:
    def analyze(self, log_text: str) -> Dict:
        return {
            "summary": {"total_events": 1, "total_errors": 0, "total_warnings": 0},
            "error_groups": [],
            "warnings": [],
            "events": []
        }


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def generate_text(self, prompt: str, system_prompt: str = None) -> str:
        self.calls += 1
        return "report"


class FakeReportWriter:
    def __init__(self):
        self.report_calls = 0

    def write_analysis(self, run_id: str, analysis: Dict) -> str:
        return f"/tmp/{run_id}.json"

    def write_report(
        self,
        run_id: str,
        report_content: str,
        report_format: str = "markdown",
        analysis: Dict = None
    ) -> str:
        self.report_calls += 1
        return f"/tmp/{run_id}.{report_format}"


class FakeCache(CachePort):
    def __init__(self):
        self.store = {}

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value, ttl_seconds: int = 60) -> None:
        self.store[key] = value

    def invalidate(self, key: str) -> None:
        self.store.pop(key, None)


def test_generate_report_uses_cache():
    settings.CACHE_ENABLED = True
    settings.CACHE_TTL_SECONDS = 60

    cache = FakeCache()
    llm = FakeLLM()
    use_case = GenerateReportUseCase(
        log_reader=FakeLogReader(),
        analyzer=FakeAnalyzer(),
        llm=llm,
        report_writer=FakeReportWriter(),
        cache=cache
    )

    use_case.execute(log_text="log", run_id="run1")
    use_case.execute(log_text="log", run_id="run1")

    assert llm.calls == 1
