"""
Modelos de dominio para log_analyzer.
Entidades y objetos de valor del dominio de análisis de logs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class ReportFormat(str, Enum):
    """Formatos soportados para descarga de reportes"""
    EXCEL = "excel"
    TXT = "txt"
    CSV = "csv"
    DOC = "doc"


@dataclass
class LogFile:
    """Representa un archivo de log disponible para análisis"""
    name: str
    path: str
    size_bytes: int
    
    def __post_init__(self):
        """Valida que el nombre no esté vacío"""
        if not self.name or not self.name.strip():
            raise ValueError("El nombre del archivo no puede estar vacío")


@dataclass
class ReportRequest:
    """Solicitud para generar y descargar un reporte"""
    report_name: str
    format: ReportFormat
    files: List[str]
    
    def __post_init__(self):
        """Valida los parámetros de la solicitud"""
        if not self.report_name or not self.report_name.strip():
            raise ValueError("El nombre del reporte no puede estar vacío")
        
        if not self.files or len(self.files) == 0:
            raise ValueError("Debe especificar al menos un archivo")
        
        if not isinstance(self.format, ReportFormat):
            raise ValueError(f"Formato no soportado: {self.format}")


@dataclass
class ReportArtifact:
    """Artefacto generado tras crear un reporte descargable"""
    name: str
    format: ReportFormat
    path: str
    size_bytes: int
    
    def __post_init__(self):
        """Valida que el path no esté vacío"""
        if not self.path or not self.path.strip():
            raise ValueError("El path del reporte no puede estar vacío")


@dataclass
class LogEvent:
    """Representa un evento individual parseado del log"""
    timestamp: str
    level: str
    thread: str
    logger: str
    message: str
    exception: Optional[str] = None
    exception_message: Optional[str] = None
    top_frame: Optional[Dict] = None
    raw_block: Optional[str] = None


@dataclass
class ErrorGroup:
    """Grupo de errores similares (misma excepción + ubicación)"""
    count: int
    exception: Optional[str]
    top_frame: Optional[Dict]
    logger: str
    samples: List[Dict]
    first_ts: str
    last_ts: str


@dataclass
class LogAnalysis:
    """Resultado del análisis estructurado de logs"""
    summary: Dict[str, int]
    error_groups: List[Dict]
    warnings: List[Dict]
    events: List[Dict]
    
    def to_dict(self) -> Dict:
        """Convierte el análisis a diccionario serializable"""
        return {
            "summary": self.summary,
            "error_groups": self.error_groups,
            "warnings": self.warnings,
            "events": self.events
        }


@dataclass
class ReportOutput:
    """Salida del proceso de generación de reporte"""
    run_id: str
    report_paths: Dict[str, str]
    analysis_path: str
    summary: Dict[str, int]
    report_format: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario para respuestas API"""
        return {
            "run_id": self.run_id,
            "report_paths": self.report_paths,
            "analysis_path": self.analysis_path,
            "summary": self.summary,
            "report_format": self.report_format,
            "timestamp": self.timestamp.isoformat()
        }
