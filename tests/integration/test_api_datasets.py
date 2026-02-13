"""
Tests de integración para el endpoint /datasets.
Verifica que la API lista correctamente los logs disponibles.
"""

import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch
from flask import Flask

from app.api import create_app


@pytest.fixture
def app_with_temp_datasets():
    """Fixture que crea una app con un directorio temporal de datasets"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Crear algunos archivos de prueba
        (Path(tmp_dir) / "app.txt").write_text("app logs")
        (Path(tmp_dir) / "system.txt").write_text("system logs")
        (Path(tmp_dir) / "debug.txt").write_text("debug logs")

        # Crear la app
        app = create_app()
        
        yield app, tmp_dir


def test_datasets_endpoint_returns_list_of_logs():
    """Debe retornar una lista de logs disponibles"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        (Path(tmp_dir) / "test.txt").write_text("test logs")
        
        app = create_app()
        
        with patch('app.api.settings.DATASETS_DIR', tmp_dir):
            with app.test_client() as client:
                response = client.get('/datasets')
                
                assert response.status_code == 200
                data = response.get_json()
                
                assert "files" in data
                assert "count" in data
                assert isinstance(data["files"], list)
                assert isinstance(data["count"], int)
                assert data["count"] >= 0


def test_datasets_endpoint_returns_correct_files():
    """Debe retornar los archivos correctos con metadatos"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Crear archivos de prueba
        (Path(tmp_dir) / "app.txt").write_text("app logs")
        (Path(tmp_dir) / "system.txt").write_text("system logs")
        (Path(tmp_dir) / "debug.txt").write_text("debug logs")
        
        app = create_app()
        
        with patch('app.api.settings.DATASETS_DIR', tmp_dir):
            with app.test_client() as client:
                response = client.get('/datasets')
                data = response.get_json()
                
                assert data["count"] == 3
                assert len(data["files"]) == 3
                
                # Verificar que cada archivo tiene los campos necesarios
                file_names = [f["name"] for f in data["files"]]
                assert "app.txt" in file_names
                assert "system.txt" in file_names
                assert "debug.txt" in file_names
                
                # Verificar estructura de cada archivo
                for file_info in data["files"]:
                    assert "name" in file_info
                    assert "size_bytes" in file_info
                    assert "path" in file_info
                    assert isinstance(file_info["size_bytes"], int)


def test_datasets_endpoint_returns_empty_list_for_empty_dir():
    """Debe retornar lista vacía cuando no hay archivos"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        app = create_app()
        
        with patch('app.api.settings.DATASETS_DIR', tmp_dir):
            with app.test_client() as client:
                response = client.get('/datasets')
                data = response.get_json()
                
                assert response.status_code == 200
                assert data["count"] == 0
                assert data["files"] == []


def test_datasets_endpoint_sorted_files():
    """Los archivos deben estar ordenados alfabéticamente"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Crear archivos en orden no alfabético
        (Path(tmp_dir) / "zebra.txt").write_text("z")
        (Path(tmp_dir) / "alpha.txt").write_text("a")
        (Path(tmp_dir) / "beta.txt").write_text("b")
        
        app = create_app()
        
        with patch('app.api.settings.DATASETS_DIR', tmp_dir):
            with app.test_client() as client:
                response = client.get('/datasets')
                data = response.get_json()
                
                file_names = [f["name"] for f in data["files"]]
                assert file_names == sorted(file_names)

