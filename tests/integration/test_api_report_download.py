"""
Integration tests for the /reports/download endpoint.
"""

import pytest

from app.api import create_app


class TestReportDownloadIntegration:
    """Integration tests for report download"""

    def test_download_returns_attachment_headers(self):
        app = create_app()

        with app.test_client() as client:
            payload = {
                "report_name": "test_report",
                "format": "txt",
                "input_text": "ERROR: Test error\nERROR: Another error",
                "llm_enabled": False
            }

            response = client.post(
                "/reports/download",
                json=payload,
                content_type="application/json"
            )

            assert response.status_code == 200
            assert "Content-Disposition" in response.headers
            assert "X-Run-Id" in response.headers

    @pytest.mark.parametrize("format_value, expected_mime", [
        ("txt", "text/plain"),
        ("csv", "text/csv"),
        ("markdown", "text/markdown"),
    ])
    def test_download_returns_expected_mime_type(self, format_value, expected_mime):
        app = create_app()

        with app.test_client() as client:
            payload = {
                "report_name": "test",
                "format": format_value,
                "input_text": "sample text",
                "llm_enabled": False
            }

            response = client.post(
                "/reports/download",
                json=payload,
                content_type="application/json"
            )

            assert response.status_code == 200
            assert expected_mime in response.content_type

    def test_download_invalid_format_returns_422(self):
        app = create_app()

        with app.test_client() as client:
            payload = {
                "report_name": "test",
                "format": "pdf",
                "input_text": "sample text",
                "llm_enabled": False
            }

            response = client.post(
                "/reports/download",
                json=payload,
                content_type="application/json"
            )

            assert response.status_code == 422
