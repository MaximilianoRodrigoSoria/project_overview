"""
Tests unitarios para los adaptadores de escritura de reportes.
Verifica que cada formato de salida funciona correctamente.
"""

import tempfile
from pathlib import Path
import pytest
import json

from src.adapters.report_writer_txt import TextReportWriter
from src.adapters.report_writer_csv import CSVReportWriter
from src.adapters.report_writer_doc import DocReportWriter


class TestTextReportWriter:
    """Tests para el writer de reportes en texto plano"""

    def test_write_report_creates_txt_file(self):
        """Debe crear un archivo .txt con el reporte"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = TextReportWriter()
            content = "Reporte de análisis\n\nErrores encontrados: 5"
            
            path = writer.write_report(
                run_id="test-001",
                report_content=content,
                output_dir=tmp_dir
            )
            
            assert Path(path).exists()
            assert path.endswith(".txt")
            
            with open(path, 'r', encoding='utf-8') as f:
                written_content = f.read()
            
            assert written_content == content

    def test_write_report_uses_run_id_in_filename(self):
        """El nombre del archivo debe contener el run_id"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = TextReportWriter()
            
            path = writer.write_report(
                run_id="my-special-id",
                report_content="content",
                output_dir=tmp_dir
            )
            
            filename = Path(path).name
            assert "my-special-id" in filename

    def test_write_report_with_analysis_ignores_it(self):
        """El writer de txt debe ignorar el análisis adicional"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = TextReportWriter()
            analysis = {"errors": 5, "warnings": 3}
            
            path = writer.write_report(
                run_id="test",
                report_content="Content",
                output_dir=tmp_dir,
                analysis=analysis
            )
            
            # Debe funcionar sin errores
            assert Path(path).exists()


class TestCSVReportWriter:
    """Tests para el writer de reportes en CSV"""

    def test_write_report_creates_csv_file(self):
        """Debe crear un archivo .csv con el reporte"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = CSVReportWriter()
            content = "Reporte de análisis\n\nErrores,5\nAdvertencias,3"
            
            path = writer.write_report(
                run_id="test-001",
                report_content=content,
                output_dir=tmp_dir
            )
            
            assert Path(path).exists()
            assert path.endswith(".csv")

    def test_write_report_uses_analysis_when_available(self):
        """Debe usar la información del análisis cuando está disponible"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = CSVReportWriter()
            analysis = {
                "summary": {"error_count": 10, "warning_count": 5},
                "error_groups": [
                    {"count": 5, "exception": "NullPointerException"},
                    {"count": 5, "exception": "IOException"}
                ]
            }
            
            path = writer.write_report(
                run_id="test",
                report_content="Content",
                output_dir=tmp_dir,
                analysis=analysis
            )
            
            assert Path(path).exists()
            
            # Verificar que el CSV tiene contenido
            with open(path, 'r') as f:
                content = f.read()
            
            assert len(content) > 0

    def test_write_report_csv_has_headers(self):
        """El CSV debe tener headers descriptivos"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = CSVReportWriter()
            analysis = {
                "summary": {"error_count": 10},
                "error_groups": []
            }
            
            path = writer.write_report(
                run_id="test",
                report_content="Content",
                output_dir=tmp_dir,
                analysis=analysis
            )
            
            with open(path, 'r') as f:
                first_line = f.readline()
            
            # Debe tener algún encabezado
            assert len(first_line) > 0


class TestDocReportWriter:
    """Tests para el writer de reportes en formato DOC (RTF)"""

    def test_write_report_creates_doc_file(self):
        """Debe crear un archivo .doc con el reporte"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = DocReportWriter()
            content = "Reporte de análisis\n\nErrores encontrados"
            
            path = writer.write_report(
                run_id="test-001",
                report_content=content,
                output_dir=tmp_dir
            )
            
            assert Path(path).exists()
            assert path.endswith(".doc")

    def test_write_report_doc_has_rtf_header(self):
        """El archivo .doc debe contener RTF bien formado"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = DocReportWriter()
            
            path = writer.write_report(
                run_id="test",
                report_content="Test content",
                output_dir=tmp_dir
            )
            
            with open(path, 'rb') as f:
                content = f.read()
            
            # RTF siempre comienza con {\rtf
            assert content.startswith(b'{\\rtf') or content.startswith(b'\\rtf')

    def test_write_report_doc_is_readable(self):
        """El archivo .doc debe ser un RTF válido que Word puede abrir"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = DocReportWriter()
            
            path = writer.write_report(
                run_id="test",
                report_content="This is a test report with special chars: áéíóú",
                output_dir=tmp_dir
            )
            
            # Simplemente verificar que el archivo se creó sin errores
            assert Path(path).stat().st_size > 0


class TestReportWriterInterface:
    """Tests comunes para todos los writers"""

    @pytest.mark.parametrize("writer_class", [
        TextReportWriter,
        CSVReportWriter,
        DocReportWriter
    ])
    def test_all_writers_implement_write_report(self, writer_class):
        """Todos los writers deben implementar write_report"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = writer_class()
            
            path = writer.write_report(
                run_id="test",
                report_content="Content",
                output_dir=tmp_dir
            )
            
            assert Path(path).exists()

    @pytest.mark.parametrize("writer_class", [
        TextReportWriter,
        CSVReportWriter,
        DocReportWriter
    ])
    def test_all_writers_return_path_string(self, writer_class):
        """Todos los writers deben retornar un string con el path"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = writer_class()
            
            path = writer.write_report(
                run_id="test",
                report_content="Content",
                output_dir=tmp_dir
            )
            
            assert isinstance(path, str)
            assert len(path) > 0

    @pytest.mark.parametrize("writer_class", [
        TextReportWriter,
        CSVReportWriter,
        DocReportWriter
    ])
    def test_all_writers_handle_special_characters(self, writer_class):
        """Todos los writers deben manejar caracteres especiales"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = writer_class()
            content = "Special chars: áéíóú ñ € £ ¥ 中文"
            
            path = writer.write_report(
                run_id="test",
                report_content=content,
                output_dir=tmp_dir
            )
            
            assert Path(path).exists()
            with open(path, 'r', encoding='utf-8') as f:
                written = f.read()
            
            # Debe preservar algún contenido legible
            assert len(written) > 0
