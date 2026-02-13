"""
Adapter para escribir reportes en formato DOC (RTF compatible).
Genera archivos RTF que pueden ser abiertos por Microsoft Word.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DocReportWriter:
    """Escribe reportes en formato DOC (RTF compatible con Word)"""
    
    def write_report(
        self,
        run_id: str,
        report_content: str,
        output_dir: str,
        analysis: Optional[Dict] = None
    ) -> str:
        """
        Escribe el reporte en formato RTF (guardado como .doc).
        Genera un documento RTF válido que Word puede abrir.
        
        Args:
            run_id: Identificador único de la ejecución
            report_content: Contenido del reporte
            output_dir: Directorio de salida
            analysis: Análisis estructurado (opcional, para enriquecer el reporte)
        
        Returns:
            Path del archivo generado
        
        Raises:
            IOError: Si hay error de escritura
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{run_id}_report.doc"
        file_path = output_path / filename
        
        logger.debug(f"Escribiendo reporte RTF/DOC a {file_path}")
        
        try:
            # Construir documento RTF válido
            rtf_content = self._generate_rtf(report_content, analysis)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(rtf_content)
            
            logger.info(f"Reporte DOC generado: {file_path}")
            return str(file_path.absolute())
        
        except Exception as e:
            logger.error(f"Error al escribir reporte DOC: {e}")
            raise IOError(f"Error al escribir archivo DOC: {e}") from e
    
    def _generate_rtf(self, report_content: str, analysis: Optional[Dict] = None) -> str:
        """
        Genera contenido RTF válido a partir del reporte.
        
        Args:
            report_content: Contenido del reporte en texto plano
            analysis: Análisis opcional
        
        Returns:
            String con documento RTF completo
        """
        # Escapar caracteres especiales para RTF
        escaped_content = self._escape_rtf(report_content)
        
        # Encabezado RTF obligatorio
        rtf = "{\\rtf1\\ansi\\ansicpg1252\\deff0\\deflang1033\n"
        
        # Tabla de fuentes
        rtf += "{\\fonttbl"
        rtf += "{\\f0\\fnil\\fcharset0 Calibri;}}\\n"
        
        # Esquema de colores
        rtf += "{\\colortbl;\\red0\\green0\\blue0;}\n"
        
        # Configuración del documento
        rtf += "\\viewkind4\\uc1\\pard\\f0\\fs20\n"
        
        # Título
        rtf += "{\\b\\fs28 Reporte de An\\\'e1lisis de Logs}\\par\\par\n"
        
        # Contenido principal
        rtf += escaped_content + "\\par\\par\n"
        
        # Análisis adicional si está disponible
        if analysis and "summary" in analysis:
            rtf += "{\\b Resumen:}\\par\n"
            for key, value in analysis["summary"].items():
                rtf += f"  {key}: {value}\\par\n"
            rtf += "\\par\n"
        
        if analysis and "error_groups" in analysis:
            rtf += "{\\b Grupos de Errores:}\\par\n"
            for group in analysis["error_groups"][:5]:  # Limitar a 5 grupos
                exception = group.get("exception", "Unknown")
                count = group.get("count", 0)
                rtf += f"  {exception}: {count} ocurrencias\\par\n"
            rtf += "\\par\n"
        
        # Pie de página
        rtf += "{\\i Generado automáticamente por Log Analyzer}\\par\n"
        
        # Cierre
        rtf += "}"
        
        return rtf
    
    def _escape_rtf(self, text: str) -> str:
        """
        Escapa caracteres especiales para RTF.
        
        Args:
            text: Texto a escapar
        
        Returns:
            Texto escapado para RTF
        """
        # Reemplazos básicos para RTF
        replacements = {
            "\\": "\\\\",      # Backslash
            "{": "\\{",        # Llave abierta
            "}": "\\}",        # Llave cerrada
            "\n": "\\par\n",   # Salto de línea
            "\t": "\\tab ",    # Tabulación
        }
        
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        # Manejar caracteres acentuados (codificarlos a octal RTF)
        safe_result = ""
        for char in result:
            code = ord(char)
            # ASCII imprimible (excepto los que ya escapamos)
            if 32 <= code <= 126 and char not in "\\{}":
                safe_result += char
            # Caracteres especiales
            elif code < 256:
                safe_result += f"\\'{'%02x' % code}"
            # Caracteres Unicode
            else:
                safe_result += f"\\u{code}?"
        
        return safe_result
