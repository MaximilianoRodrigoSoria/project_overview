"""
Esquema de reporte para log_analyzer.
"""

from typing import Dict, List


def get_report_schema() -> Dict[str, List[Dict[str, str]]]:
    """
    Retorna el esquema base del reporte Excel.

    Returns:
        Diccionario con secciones y columnas
    """
    return {
        "summary": [
            {"key": "total_events", "label": "Total eventos"},
            {"key": "total_errors", "label": "Errores"},
            {"key": "total_warnings", "label": "Warnings"}
        ],
        "error_groups": [
            {"key": "exception", "label": "Excepcion"},
            {"key": "count", "label": "Cantidad"},
            {"key": "logger", "label": "Logger"},
            {"key": "first_ts", "label": "Primer timestamp"},
            {"key": "last_ts", "label": "Ultimo timestamp"}
        ],
        "warnings": [
            {"key": "ts", "label": "Timestamp"},
            {"key": "logger", "label": "Logger"},
            {"key": "message", "label": "Mensaje"}
        ]
    }
