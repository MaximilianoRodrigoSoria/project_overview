"""
Contract tests for the /reports/download endpoint.
"""

import pytest

from app.api import create_app


class TestReportDownloadEndpoint:
    """Contract tests for POST /reports/download"""

    def test_download_endpoint_accepts_json_request(self):
        """Accepts JSON with report_name, format, input_text, llm_enabled"""
        app = create_app()

        with app.test_client() as client:
            payload = {
                "report_name": "test_report",
                "format": "txt",
                "input_text": "sample text",
                "llm_enabled": False
            }

            response = client.post(
                "/reports/download",
                json=payload,
                content_type="application/json"
            )

            assert response.status_code == 200

    @pytest.mark.parametrize("field", [
        "report_name",
        "format",
        "input_text",
        "llm_enabled",
    ])
    def test_download_endpoint_requires_fields(self, field):
        """Rejects requests missing required fields"""
        app = create_app()

        payload = {
            "report_name": "test",
            "format": "txt",
            "input_text": "sample",
            "llm_enabled": False
        }
        payload.pop(field)

        with app.test_client() as client:
            response = client.post(
                "/reports/download",
                json=payload,
                content_type="application/json"
            )

            assert response.status_code == 400

    def test_download_endpoint_validates_format(self):
        """Rejects unsupported formats"""
        app = create_app()

        with app.test_client() as client:
            payload = {
                "report_name": "test",
                "format": "pdf",
                "input_text": "sample",
                "llm_enabled": False
            }

            response = client.post(
                "/reports/download",
                json=payload,
                content_type="application/json"
            )

            assert response.status_code == 422

    @pytest.mark.parametrize("format_value", ["excel", "txt", "csv", "markdown", "doc"])
    def test_download_endpoint_supports_formats(self, format_value):
        """Accepts all supported formats"""
        app = create_app()

        with app.test_client() as client:
            payload = {
                "report_name": "test",
                "format": format_value,
                "input_text": "sample",
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
                    
                    assert response.status_code != 400

    def test_download_endpoint_supports_doc_format(self):
        """Debe aceptar format: doc"""
        app = create_app()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            test_file.write_text("test content")
            
            with patch('app.api.settings.DATASETS_DIR', tmp_dir):
                with app.test_client() as client:
                    payload = {
                        "report_name": "test",
                        "format": "doc",
                        "files": ["test.txt"]
                    }
                    
                    response = client.post(
                        '/reports/download',
                        json=payload,
                        content_type='application/json'
                    )
                    
                    assert response.status_code != 400

    def test_download_endpoint_returns_json_on_error(self):
        """Debe retornar JSON con error en caso de fallo"""
        app = create_app()
        
        with app.test_client() as client:
            payload = {
                "report_name": "test",
                "format": "xlsx",  # Inválido
                "files": ["test.txt"]
            }
            
            response = client.post(
                '/reports/download',
                json=payload,
                content_type='application/json'
            )
            
            assert response.content_type == "application/json" or response.status_code == 400

    def test_download_endpoint_missing_files_returns_404(self):
        """Debe retornar 404 cuando los archivos no existen"""
        app = create_app()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch('app.api.settings.DATASETS_DIR', tmp_dir):
                with app.test_client() as client:
                    payload = {
                        "report_name": "test",
                        "format": "txt",
                        "files": ["nonexistent.txt"]
                    }
                    
                    response = client.post(
                        '/reports/download',
                        json=payload,
                        content_type='application/json'
                    )
                    
                    assert response.status_code == 404
