"""
Tests unitarios para FileSystemLogReader.
Verifica lectura de archivos y listado de logs desde filesystem.
"""

import pytest
import tempfile
from pathlib import Path

from src.adapters.log_reader_fs import FileSystemLogReader


class TestListLogs:
    """Tests para el método list_logs"""

    def test_list_logs_returns_empty_list_for_empty_directory(self):
        """Debe retornar lista vacía cuando no hay archivos .txt en el directorio"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            reader = FileSystemLogReader()
            result = reader.list_logs(tmp_dir)
            assert result == []

    def test_list_logs_returns_single_file(self):
        """Debe retornar un archivo cuando existe un .txt en el directorio"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Crear un archivo de prueba
            test_file = Path(tmp_dir) / "test.txt"
            test_content = "test content"
            test_file.write_text(test_content)

            reader = FileSystemLogReader()
            result = reader.list_logs(tmp_dir)

            assert len(result) == 1
            assert result[0]["name"] == "test.txt"
            assert result[0]["size_bytes"] == len(test_content)
            assert "path" in result[0]

    def test_list_logs_returns_multiple_files_sorted(self):
        """Debe retornar múltiples archivos .txt ordenados alfabéticamente"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Crear múltiples archivos en orden no alfabético
            files = ["zebra.txt", "alpha.txt", "beta.txt"]
            for fname in files:
                Path(tmp_dir) / fname
                (Path(tmp_dir) / fname).write_text(f"content of {fname}")

            reader = FileSystemLogReader()
            result = reader.list_logs(tmp_dir)

            assert len(result) == 3
            # Verificar que están ordenados
            names = [f["name"] for f in result]
            assert names == ["alpha.txt", "beta.txt", "zebra.txt"]

    def test_list_logs_ignores_non_txt_files(self):
        """Debe ignorar archivos que no sean .txt"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            Path(tmp_dir) / "keep.txt"
            (Path(tmp_dir) / "keep.txt").write_text("keep this")
            (Path(tmp_dir) / "skip.log").write_text("skip this")
            (Path(tmp_dir) / "skip.md").write_text("skip this too")

            reader = FileSystemLogReader()
            result = reader.list_logs(tmp_dir)

            assert len(result) == 1
            assert result[0]["name"] == "keep.txt"

    def test_list_logs_ignores_directories(self):
        """Debe ignorar subdirectorios aunque tengan nombres .txt"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "keep.txt").write_text("file")
            (Path(tmp_dir) / "skip.txt").mkdir()  # directorio, no archivo

            reader = FileSystemLogReader()
            result = reader.list_logs(tmp_dir)

            assert len(result) == 1
            assert result[0]["name"] == "keep.txt"

    def test_list_logs_raises_file_not_found_for_missing_directory(self):
        """Debe lanzar FileNotFoundError si el directorio no existe"""
        reader = FileSystemLogReader()
        with pytest.raises(FileNotFoundError):
            reader.list_logs("/nonexistent/directory/path")

    def test_list_logs_raises_value_error_for_file_path(self):
        """Debe lanzar ValueError si se pasa un archivo en lugar de directorio"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            test_file.write_text("content")

            reader = FileSystemLogReader()
            with pytest.raises(ValueError):
                reader.list_logs(str(test_file))

    def test_list_logs_returns_dict_with_required_keys(self):
        """Debe retornar dicts con las claves name, path, size_bytes"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "test.txt").write_text("content")

            reader = FileSystemLogReader()
            result = reader.list_logs(tmp_dir)

            assert len(result) == 1
            item = result[0]
            assert "name" in item
            assert "path" in item
            assert "size_bytes" in item
            assert isinstance(item["size_bytes"], int)
            assert item["size_bytes"] >= 0


class TestReadLog:
    """Tests para el método read_log (regresión)"""

    def test_read_log_returns_content(self):
        """Debe retornar el contenido completo del archivo"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            content = "line 1\nline 2\nline 3"
            test_file.write_text(content)

            reader = FileSystemLogReader()
            result = reader.read_log(str(test_file))

            assert result == content

    def test_read_log_raises_file_not_found(self):
        """Debe lanzar FileNotFoundError si el archivo no existe"""
        reader = FileSystemLogReader()
        with pytest.raises(FileNotFoundError):
            reader.read_log("/nonexistent/file.txt")

    def test_read_log_raises_value_error_for_directory(self):
        """Debe lanzar ValueError si se pasa un directorio en lugar de archivo"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            reader = FileSystemLogReader()
            with pytest.raises(ValueError):
                reader.read_log(tmp_dir)
