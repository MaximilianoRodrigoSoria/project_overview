"""
DTOs (Data Transfer Objects) para el endpoint /analyze.
Define estructuras de request y response con validación.
"""

import os
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path

from .enums import OutputFormat


@dataclass
class AnalyzeRequest:
    """
    DTO para la solicitud de análisis de logs.
    Incluye validación y sanitización de inputs.
    """
    input_log_filename: str
    output_filename: str
    output_format: OutputFormat
    run_id: Optional[str] = None
    
    def __post_init__(self):
        """Valida y sanitiza los parámetros después de la creación"""
        # Validar input_log_filename
        if not self.input_log_filename or not self.input_log_filename.strip():
            raise ValueError("Campo 'input_log_filename' es requerido y no puede estar vacío")
        
        # Sanitizar input_log_filename (solo basename, no paths)
        self.input_log_filename = os.path.basename(self.input_log_filename)
        
        # Validar output_filename
        if not self.output_filename or not self.output_filename.strip():
            raise ValueError("Campo 'output_filename' es requerido y no puede estar vacío")
        
        # Sanitizar output_filename (prevenir path traversal)
        self.output_filename = self._sanitize_filename(self.output_filename)
        
        # Validar output_format
        if not isinstance(self.output_format, OutputFormat):
            raise ValueError(
                f"Campo 'output_format' debe ser uno de: {', '.join(OutputFormat.values())}"
            )
        
        # Generar run_id si no viene
        if not self.run_id:
            from uuid import uuid4
            self.run_id = uuid4().hex[:12]
        else:
            # Sanitizar run_id si viene (prevenir path traversal)
            self.run_id = self._sanitize_filename(self.run_id)
    
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        Sanitiza un nombre de archivo para prevenir path traversal.
        Remueve caracteres peligrosos y limita a basename.
        
        Args:
            name: Nombre a sanitizar
        
        Returns:
            Nombre sanitizado
        """
        # Remover cualquier path (solo mantener el basename)
        name = os.path.basename(name)
        
        # Remover caracteres peligrosos (permitir alfanuméricos, guiones, guiones bajos y puntos)
        name = re.sub(r'[^\w\-\.]', '_', name)
        
        # Prevenir nombres de archivo ocultos
        if name.startswith('.'):
            name = '_' + name[1:]
        
        # Limitar longitud
        if len(name) > 100:
            name = name[:100]
        
        return name
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyzeRequest':
        """
        Crea una instancia desde un diccionario (para parsing de JSON).
        
        Args:
            data: Diccionario con los datos del request
        
        Returns:
            Instancia de AnalyzeRequest
        
        Raises:
            ValueError: Si falta algún campo requerido o el formato es inválido
        """
        # Validar campos requeridos
        required_fields = ['input_log_filename', 'output_filename', 'output_format']
        missing = [field for field in required_fields if field not in data or data[field] is None]
        
        if missing:
            raise ValueError(f"Campos requeridos faltantes: {', '.join(missing)}")
        
        # Parsear output_format
        output_format_str = data.get('output_format', '').lower()
        
        if not OutputFormat.is_valid(output_format_str):
            raise ValueError(
                f"Valor inválido para 'output_format': '{output_format_str}'. "
                f"Valores permitidos: {', '.join(OutputFormat.values())}"
            )
        
        output_format = OutputFormat(output_format_str)
        
        # Crear instancia (run_id es opcional, se genera automáticamente si no viene)
        return cls(
            input_log_filename=str(data['input_log_filename']),
            output_filename=str(data['output_filename']),
            output_format=output_format,
            run_id=data.get('run_id')  # Opcional
        )


@dataclass
class AnalyzeResponse:
    """
    DTO para la respuesta del endpoint de análisis.
    Estructura consistente para respuestas exitosas y errores.
    """
    status: str
    run_id: str
    output_path: Optional[str] = None
    output_format: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    errors: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la respuesta a diccionario para serialización JSON.
        
        Returns:
            Diccionario con los datos de la respuesta
        """
        result = {
            'status': self.status,
            'run_id': self.run_id
        }
        
        if self.output_path is not None:
            result['output_path'] = self.output_path
        
        if self.output_format is not None:
            result['output_format'] = self.output_format
        
        if self.summary is not None:
            result['summary'] = self.summary
        
        if self.errors is not None:
            result['errors'] = self.errors
        
        return result
    
    @classmethod
    def success(
        cls,
        run_id: str,
        output_path: str,
        output_format: str,
        summary: Optional[Dict[str, Any]] = None
    ) -> 'AnalyzeResponse':
        """
        Crea una respuesta exitosa.
        
        Args:
            run_id: Identificador de la ejecución
            output_path: Ruta del archivo generado
            output_format: Formato del archivo generado
            summary: Resumen del análisis (opcional)
        
        Returns:
            Instancia de AnalyzeResponse con status success
        """
        return cls(
            status='success',
            run_id=run_id,
            output_path=output_path,
            output_format=output_format,
            summary=summary or {},
            errors=None
        )
    
    @classmethod
    def error(
        cls,
        run_id: str,
        error_message: str
    ) -> 'AnalyzeResponse':
        """
        Crea una respuesta de error.
        
        Args:
            run_id: Identificador de la ejecución
            error_message: Mensaje de error
        
        Returns:
            Instancia de AnalyzeResponse con status error
        """
        return cls(
            status='error',
            run_id=run_id,
            output_path=None,
            output_format=None,
            summary=None,
            errors=error_message
        )


@dataclass
class ErrorResponse:
    """
    DTO para respuestas de error estructuradas.
    """
    code: int
    message: str
    details: Optional[str] = None
    run_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para JSON"""
        result = {
            'code': self.code,
            'message': self.message
        }
        
        if self.details is not None:
            result['details'] = self.details
        
        if self.run_id is not None:
            result['run_id'] = self.run_id
        
        return result
