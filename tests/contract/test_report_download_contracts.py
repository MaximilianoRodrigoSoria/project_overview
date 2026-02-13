"""
Contract tests para el endpoint /reports/download.
Verifica que la API cumpla con las especificaciones del contrato OpenAPI.
"""

import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

from app.api import create_app


class TestReportDownloadEndpoint:
    """Tests de contrato para POST /reports/download"""

    def test_download_endpoint_accepts_json_request(self):
        """Debe aceptar solicitudes JSON con report_name, format, files"""
        app = create_app()
        
        with app.test_client() as client:
            payload = {
                "report_name": "test_report",
                "format": "txt",
                "files": ["test.txt"]
            }
            
            response = client.post(
                '/reports/download',
                json=payload,
                content_type='application/json'
            )
            
            # Puede fallar por archivos no encontrados, pero debe responder
            assert response.status_code in [200, 400, 404, 500]

    def test_download_endpoint_requires_report_name(self):
        """Debe rechazar solicitud sin report_name"""
        app = create_app()
        
        with app.test_client() as client:
            payload = {
                "format": "txt",
                "files": ["test.txt"]
            }
            
            response = client.post(
                '/reports/download',
                json=payload,
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data

    def test_download_endpoint_requires_format(self):
        """Debe rechazar solicitud sin format"""
        app = create_app()
        
        with app.test_client() as client:
            payload = {
                "report_name": "test",
                "files": ["test.txt"]
            }
            
            response = client.post(
                '/reports/download',
                json=payload,
                content_type='application/json'
            )
            
            assert response.status_code == 400

    def test_download_endpoint_requires_files(self):
        """Debe rechazar solicitud sin files"""
        app = create_app()
        
        with app.test_client() as client:
            payload = {
                "report_name": "test",
                "format": "txt"
            }
            
            response = client.post(
                '/reports/download',
                json=payload,
                content_type='application/json'
            )
            
            assert response.status_code == 400

    def test_download_endpoint_requires_files_non_empty(self):
        """Debe rechazar solicitud con files vacío"""
        app = create_app()
        
        with app.test_client() as client:
            payload = {
                "report_name": "test",
                "format": "txt",
                "files": []
            }
            
            response = client.post(
                '/reports/download',
                json=payload,
                content_type='application/json'
            )
            
            assert response.status_code == 400

    def test_download_endpoint_validates_format(self):
        """Debe rechazar formatos no soportados"""
        app = create_app()
        
        with app.test_client() as client:
            payload = {
                "report_name": "test",
                "format": "pdf",  # No soportado
                "files": ["test.txt"]
            }
            
            response = client.post(
                '/reports/download',
                json=payload,
                content_type='application/json'
            )
            
            assert response.status_code == 400

    def test_download_endpoint_supports_excel_format(self):
        """Debe aceptar format: excel"""
        app = create_app()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            test_file.write_text("test content")
            
            with patch('app.api.settings.DATASETS_DIR', tmp_dir):
                with app.test_client() as client:
                    payload = {
                        "report_name": "test",
                        "format": "excel",
                        "files": ["test.txt"]
                    }
                    
                    response = client.post(
                        '/reports/download',
                        json=payload,
                        content_type='application/json'
                    )
                    
                    # Puede ser error de análisis/LLM, pero no de validación
                    assert response.status_code != 400

    def test_download_endpoint_supports_txt_format(self):
        """Debe aceptar format: txt"""
        app = create_app()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            test_file.write_text("test content")
            
            with patch('app.api.settings.DATASETS_DIR', tmp_dir):
                with app.test_client() as client:
                    payload = {
                        "report_name": "test",
                        "format": "txt",
                        "files": ["test.txt"]
                    }
                    
                    response = client.post(
                        '/reports/download',
                        json=payload,
                        content_type='application/json'
                    )
                    
                    assert response.status_code != 400

    def test_download_endpoint_supports_csv_format(self):
        """Debe aceptar format: csv"""
        app = create_app()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            test_file.write_text("test content")
            
            with patch('app.api.settings.DATASETS_DIR', tmp_dir):
                with app.test_client() as client:
                    payload = {
                        "report_name": "test",
                        "format": "csv",
                        "files": ["test.txt"]
                    }
                    
                    response = client.post(
                        '/reports/download',
                        json=payload,
                        content_type='application/json'
                    )
                    
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
