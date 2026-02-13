"""
Integration tests for the Flask API.
"""

from dataclasses import dataclass

from app import api as api_module


@dataclass
class ReportOutput:
    run_id: str
    report_paths: dict
    analysis_path: str
    summary: dict
    report_format: str


class FakeUseCase:
    """Simple test double for GenerateReportUseCase."""

    def __init__(self):
        self.calls = []

    def execute(self, log_text=None, log_path=None, run_id=None):
        self.calls.append({
            "log_text": log_text,
            "log_path": log_path,
            "run_id": run_id,
        })
        return ReportOutput(
            run_id=run_id or "test-run",
            report_paths={"excel": "out/reports/test.xlsx"},
            analysis_path="out/analysis/test.json",
            summary={
                "total_events": 1,
                "total_errors": 0,
                "total_warnings": 0,
            },
            report_format="excel",
        )


def test_analyze_with_log_text(monkeypatch):
    fake_use_case = FakeUseCase()
    monkeypatch.setattr(api_module, "use_case", fake_use_case)

    api_module.app.testing = True
    client = api_module.app.test_client()

    response = client.post(
        "/analyze",
        json={
            "log_text": "2026-02-13 08:30:15 ERROR [main] test",
            "run_id": "run-123",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["run_id"] == "run-123"
    assert payload["report_format"] == "excel"
    assert payload["analysis_path"] == "out/analysis/test.json"
    assert payload["report_paths"]["excel"] == "out/reports/test.xlsx"

    assert fake_use_case.calls
    assert fake_use_case.calls[0]["log_text"] is not None
    assert fake_use_case.calls[0]["log_path"] is None


def test_analyze_requires_input(monkeypatch):
    fake_use_case = FakeUseCase()
    monkeypatch.setattr(api_module, "use_case", fake_use_case)

    api_module.app.testing = True
    client = api_module.app.test_client()

    response = client.post("/analyze", json={})

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["status"] == "error"
    assert "log_filename" in payload["error"]
