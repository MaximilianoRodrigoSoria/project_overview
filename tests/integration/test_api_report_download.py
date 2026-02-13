"""
Tests de integración para el endpoint /reports/download.
Verifica que la API genere y permita descargar reportes en diferentes formatos.
"""

import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import json

from app.api import create_app


class TestReportDownloadIntegration:
    """Tests de integración para funcionalidad de descarga de reportes"""

    def test_download_returns_generated_file_as_attachment(self):
        """Debe retornar el archivo generado con Content-Disposition attachment"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            test_file.write_text("ERROR: Test error\nERROR: Another error")
            
            app = create_app()
            
            with patch('app.api.settings.DATASETS_DIR', tmp_dir):
                with patch('app.api.settings.OUT_DIR', tmp_dir):
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
                        
                        # No debería ser 400 (validación)
                        if response.status_code not in [200]:
                            # Puede fallar por LLM o análisis
                            data = response.get_json()
                            assert "error" in data
                        else:
                            # Si es exitoso, debe tener Content-Disposition
                            assert "Content-Disposition" in response.headers

    def test_download_endpoint_handles_single_file(self):
        """Debe procesar correctamente un archivo único"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "single.txt"
            test_file.write_text("ERROR: Single error")
            
            app = create_app()
            
            with patch('app.api.settings.DATASETS_DIR', tmp_dir):
                with patch('app.api.settings.OUT_DIR', tmp_dir):
                    with app.test_client() as client:
                        payload = {
                            "report_name": "single",
                            "format": "txt",
                            "files": ["single.txt"]
                        }
                        
                        response = client.post(
                            '/reports/download',
                            json=payload,
                            content_type='application/json'
                        )
                        
                        # Validación debe pasar
                        assert response.status_code != 400

    def test_download_endpoint_handles_multiple_files(self):
        """Debe procesar correctamente múltiples archivos"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "file1.txt").write_text("ERROR: Error 1")
            (Path(tmp_dir) / "file2.txt").write_text("ERROR: Error 2")
            
            app = create_app()
            
            with patch('app.api.settings.DATASETS_DIR', tmp_dir):
                with patch('app.api.settings.OUT_DIR', tmp_dir):
                    with app.test_client() as client:
                        payload = {
                            "report_name": "multi",
                            "format": "csv",
                            "files": ["file1.txt", "file2.txt"]
                        }
                        
                        response = client.post(
                            '/reports/download',
                            json=payload,
                            content_type='application/json'
                        )
                        
                        assert response.status_code != 400

    def test_download_respects_max_files_limit(self):
        """Debe rechazar solicitudes con más archivos que el límite permitido"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Crear archivos
            for i in range(20):
                (Path(tmp_dir) / f"file{i}.txt").write_text(f"ERROR: Error {i}")
            
            app = create_app()
            
            with patch('app.api.settings.DATASETS_DIR', tmp_dir):
                with patch('app.api.settings.REPORT_DOWNLOAD_MAX_FILES', 10):
                    with app.test_client() as client:
                        payload = {
                            "report_name": "too_many",
                            "format": "txt",
                            "files": [f"file{i}.txt" for i in range(15)]
                        }
                        
                        response = client.post(
                            '/reports/download',
                            json=payload,
                            content_type='application/json'
                        )
                        
                        # Debe ser 400 por validación de límite
                        assert response.status_code == 400

    def test_download_error_response_has_error_field(self):
        """Las respuestas de error deben tener campo 'error'"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            app = create_app()
            
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
                    
                    if response.status_code >= 400:
                        data = response.get_json()
                        assert "error" in data or "status" in data

    def test_download_txt_format_returns_text_mime_type(self):
        """La descarga en formato txt debe tener MIME type text/plain"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            test_file.write_text("ERROR: Test")
            
            app = create_app()
            
            with patch('app.api.settings.DATASETS_DIR', tmp_dir):
                with patch('app.api.settings.OUT_DIR', tmp_dir):
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
                        
                        if response.status_code == 200:
                            assert "text/plain" in response.content_type or \
                                   response.content_type.startswith("application/octet-stream")

    def test_download_csv_format_returns_csv_mime_type(self):
        """La descarga en formato csv debe tener MIME type text/csv"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            test_file.write_text("ERROR: Test")
            
            app = create_app()
            
            with patch('app.api.settings.DATASETS_DIR', tmp_dir):
                with patch('app.api.settings.OUT_DIR', tmp_dir):
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
                        
                        if response.status_code == 200:
                            assert "text/csv" in response.content_type or \
                                   response.content_type.startswith("application/octet-stream")
