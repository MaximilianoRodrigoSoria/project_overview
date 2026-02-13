"""
Adapter de análisis de logs usando regex.
Delega en el analizador del dominio.
"""

from typing import Dict

from ..ports.analyzer_port import AnalyzerPort
from ..domain.log_analyzer.analyzer import LogAnalyzer


class RegexLogAnalyzer(AnalyzerPort):
    """Analizador de logs basado en expresiones regulares"""

    def __init__(self):
        self._analyzer = LogAnalyzer()

    def analyze(self, log_text: str) -> Dict:
        """Delegar analisis al dominio"""
        return self._analyzer.analyze(log_text)
