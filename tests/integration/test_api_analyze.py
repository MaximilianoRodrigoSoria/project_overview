"""
Integration tests for the Flask API.
"""

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from app import api as api_module


@dataclass
class AnalyzeResult:
    status: str
    output_path: str
    output_format: str
    summary: dict
    errors: str = None


class FakeAnalyzeUseCase:
    """Simple test double for AnalyzeLogUseCase."""

    def __init__(self, output_path: str):
        self.calls = []
        self.output_path = output_path

    def execute(self, analyze_request):
        self.calls.append(analyze_request)
        return AnalyzeResult(
            status="success",
            output_path=self.output_path,
            output_format=analyze_request.output_format.value,
            summary={
                "total_events": 1,
                "total_errors": 0,
                "total_warnings": 0,
            }
        )


def test_analyze_with_log_text(monkeypatch):
    with TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "report.xlsx"
        output_path.write_text("dummy")

        fake_use_case = FakeAnalyzeUseCase(str(output_path))
        monkeypatch.setattr(api_module, "analyze_use_case", fake_use_case)

        api_module.app.testing = True
        client = api_module.app.test_client()

        response = client.post(
            "/analyze",
            json={
                "input_log_filename": "generated_logs.txt",
                "output_filename": "report",
                "output_format": "excel",
                "run_id": "run-123",
            },
        )

        assert response.status_code == 200
        assert "Content-Disposition" in response.headers

        response.close()

        assert fake_use_case.calls


def test_analyze_requires_input(monkeypatch):
    fake_use_case = FakeAnalyzeUseCase("/tmp/report.xlsx")
    monkeypatch.setattr(api_module, "analyze_use_case", fake_use_case)

    api_module.app.testing = True
    client = api_module.app.test_client()

    response = client.post("/analyze", json={})

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["code"] == 400
    assert payload["message"] == "Error de validación"
