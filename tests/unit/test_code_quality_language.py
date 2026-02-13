"""Tests unitarios para soporte de idioma en Code Quality Audit."""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

from src.domain.code_quality.dtos import CodeQualityReportRequest, CodeQualityMetrics
from src.domain.code_quality.enums import ReportLanguage, ProjectTechnology
from src.domain.code_quality.use_case import GenerateCodeQualityReportUseCase
from src.domain.reporting.enums import ReportFormat
from src.domain.reporting.exceptions import ValidationError


class TestReportLanguageEnum:
    """Tests para el enum ReportLanguage."""
    
    def test_default_language_is_es_ar(self):
        """El idioma por defecto debe ser es-AR."""
        assert ReportLanguage.default() == ReportLanguage.ES_AR
        assert ReportLanguage.default().value == "es-AR"
    
    def test_valid_languages(self):
        """Debe validar correctamente los idiomas soportados."""
        assert ReportLanguage.is_valid("es-AR")
        assert ReportLanguage.is_valid("es")
        assert ReportLanguage.is_valid("en")
    
    def test_invalid_languages(self):
        """Debe rechazar idiomas no soportados."""
        assert not ReportLanguage.is_valid("fr")
        assert not ReportLanguage.is_valid("de")
        assert not ReportLanguage.is_valid("pt")
        assert not ReportLanguage.is_valid("es-MX")
        assert not ReportLanguage.is_valid("")
        assert not ReportLanguage.is_valid(None)
    
    def test_enum_values(self):
        """Debe retornar todos los valores válidos."""
        values = ReportLanguage.values()
        assert "es-AR" in values
        assert "es" in values
        assert "en" in values
        assert len(values) == 3


class TestCodeQualityReportRequestLanguage:
    """Tests para el campo language en CodeQualityReportRequest."""
    
    def test_default_language_when_not_provided(self, tmp_path):
        """Cuando no se provee language, debe usar es-AR por defecto."""
        request = CodeQualityReportRequest(
            report_name="test_report",
            format=ReportFormat.EXCEL,
            project_path=str(tmp_path)
        )
        
        assert request.language == ReportLanguage.ES_AR
    
    def test_explicit_language_es_ar(self, tmp_path):
        """Debe aceptar language=es-AR explícitamente."""
        request = CodeQualityReportRequest(
            report_name="test_report",
            format=ReportFormat.EXCEL,
            project_path=str(tmp_path),
            language=ReportLanguage.ES_AR
        )
        
        assert request.language == ReportLanguage.ES_AR
    
    def test_explicit_language_es(self, tmp_path):
        """Debe aceptar language=es."""
        request = CodeQualityReportRequest(
            report_name="test_report",
            format=ReportFormat.EXCEL,
            project_path=str(tmp_path),
            language=ReportLanguage.ES
        )
        
        assert request.language == ReportLanguage.ES
    
    def test_explicit_language_en(self, tmp_path):
        """Debe aceptar language=en."""
        request = CodeQualityReportRequest(
            report_name="test_report",
            format=ReportFormat.EXCEL,
            project_path=str(tmp_path),
            language=ReportLanguage.EN
        )
        
        assert request.language == ReportLanguage.EN
    
    def test_invalid_language_raises_validation_error(self, tmp_path):
        """Debe lanzar ValidationError con idioma inválido."""
        with pytest.raises(ValidationError) as exc_info:
            CodeQualityReportRequest(
                report_name="test_report",
                format=ReportFormat.EXCEL,
                project_path=str(tmp_path),
                language="fr"  # type: ignore
            )
        
        assert "Invalid language" in str(exc_info.value)
        assert "fr" in str(exc_info.value)
    
    def test_from_dict_with_default_language(self, tmp_path):
        """from_dict debe usar es-AR cuando language no está en el dict."""
        data = {
            "report_name": "test_report",
            "format": "excel",
            "project_path": str(tmp_path)
        }
        
        request = CodeQualityReportRequest.from_dict(data)
        assert request.language == ReportLanguage.ES_AR
    
    def test_from_dict_with_explicit_language_es_ar(self, tmp_path):
        """from_dict debe aceptar language=es-AR."""
        data = {
            "report_name": "test_report",
            "format": "excel",
            "project_path": str(tmp_path),
            "language": "es-AR"
        }
        
        request = CodeQualityReportRequest.from_dict(data)
        assert request.language == ReportLanguage.ES_AR
    
    def test_from_dict_with_explicit_language_es(self, tmp_path):
        """from_dict debe aceptar language=es."""
        data = {
            "report_name": "test_report",
            "format": "excel",
            "project_path": str(tmp_path),
            "language": "es"
        }
        
        request = CodeQualityReportRequest.from_dict(data)
        assert request.language == ReportLanguage.ES
    
    def test_from_dict_with_explicit_language_en(self, tmp_path):
        """from_dict debe aceptar language=en."""
        data = {
            "report_name": "test_report",
            "format": "excel",
            "project_path": str(tmp_path),
            "language": "en"
        }
        
        request = CodeQualityReportRequest.from_dict(data)
        assert request.language == ReportLanguage.EN
    
    def test_from_dict_with_invalid_language(self, tmp_path):
        """from_dict debe lanzar ValidationError con idioma inválido."""
        data = {
            "report_name": "test_report",
            "format": "excel",
            "project_path": str(tmp_path),
            "language": "fr"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CodeQualityReportRequest.from_dict(data)
        
        assert "Invalid language" in str(exc_info.value)
        assert "fr" in str(exc_info.value)


class TestUseCaseLanguagePrompt:
    """Tests para verificar que el UseCase genera prompts con instrucciones de idioma."""
    
    def test_build_system_prompt_with_es_ar(self):
        """El system prompt debe contener instrucciones para español argentino."""
        use_case = GenerateCodeQualityReportUseCase()
        
        system_prompt = use_case._build_system_prompt(ReportLanguage.ES_AR)
        
        assert "Spanish (Argentina)" in system_prompt
        assert "Argentine professional tone" in system_prompt
        assert "Do not translate technical names" in system_prompt
        assert "Spring Boot" in system_prompt
    
    def test_build_system_prompt_with_es(self):
        """El system prompt debe contener instrucciones para español neutro."""
        use_case = GenerateCodeQualityReportUseCase()
        
        system_prompt = use_case._build_system_prompt(ReportLanguage.ES)
        
        assert "Spanish (neutral international)" in system_prompt
        assert "neutral technical Spanish" in system_prompt
        assert "Do not translate technical names" in system_prompt
    
    def test_build_system_prompt_with_en(self):
        """El system prompt debe contener instrucciones para inglés."""
        use_case = GenerateCodeQualityReportUseCase()
        
        system_prompt = use_case._build_system_prompt(ReportLanguage.EN)
        
        assert "English" in system_prompt
        assert "professional technical English" in system_prompt
    
    def test_build_llm_prompt_with_es_language(self):
        """El prompt debe estar en español cuando language es es-AR o es."""
        use_case = GenerateCodeQualityReportUseCase()
        
        metrics = CodeQualityMetrics(
            total_files=10,
            total_lines=1000,
            avg_lines_per_file=100.0,
            technology=ProjectTechnology.PYTHON
        )
        
        prompt_es_ar = use_case._build_llm_prompt(
            ProjectTechnology.PYTHON,
            metrics,
            ReportLanguage.ES_AR
        )
        
        prompt_es = use_case._build_llm_prompt(
            ProjectTechnology.PYTHON,
            metrics,
            ReportLanguage.ES
        )
        
        # Ambos deben estar en español con estructura profesional
        assert "Actuá como Arquitecto de Software Senior" in prompt_es_ar
        assert "Informe de Calidad de Código" in prompt_es_ar
        assert "Resumen Ejecutivo" in prompt_es_ar
        assert "Análisis Estructural" in prompt_es_ar
        assert "Riesgos Técnicos Detectados" in prompt_es_ar
        assert "Recomendaciones Accionables" in prompt_es_ar
        
        # Verificar datos incluidos
        assert "total_files: 10" in prompt_es_ar
        assert "total_lines: 1000" in prompt_es_ar
        assert "avg_lines_per_file: 100.0" in prompt_es_ar
        
        # Mismo check para es
        assert "Actuá como Arquitecto de Software Senior" in prompt_es
        assert "Informe de Calidad de Código" in prompt_es
    
    def test_build_llm_prompt_with_en_language(self):
        """El prompt debe estar en inglés cuando language es en."""
        use_case = GenerateCodeQualityReportUseCase()
        
        metrics = CodeQualityMetrics(
            total_files=10,
            total_lines=1000,
            avg_lines_per_file=100.0,
            technology=ProjectTechnology.PYTHON
        )
        
        prompt = use_case._build_llm_prompt(
            ProjectTechnology.PYTHON,
            metrics,
            ReportLanguage.EN
        )
        
        assert "Analyze the following code quality metrics" in prompt
        assert "Please provide" in prompt
    
    def test_generate_narrative_calls_with_correct_language(self, tmp_path):
        """El método _generate_narrative debe pasar el idioma correctamente."""
        # Mock del LLM
        mock_llm = Mock()
        mock_llm.generate_text = Mock(return_value="Test narrative")
        
        use_case = GenerateCodeQualityReportUseCase(llm=mock_llm)
        
        metrics = CodeQualityMetrics(
            total_files=10,
            total_lines=1000,
            avg_lines_per_file=100.0,
            technology=ProjectTechnology.PYTHON
        )
        
        # Generar narrativa con es-AR
        narrative = use_case._generate_narrative(
            run_id="test-run",
            technology=ProjectTechnology.PYTHON,
            metrics=metrics,
            language=ReportLanguage.ES_AR
        )
        
        # Verificar que se llamó al LLM
        assert mock_llm.generate_text.called
        
        # Verificar que los argumentos contienen las instrucciones de idioma
        call_args = mock_llm.generate_text.call_args
        system_prompt = call_args.kwargs.get('system_prompt')
        prompt = call_args.kwargs.get('prompt')
        
        assert "Spanish (Argentina)" in system_prompt
        assert "Actuá como Arquitecto de Software Senior" in prompt
        assert "Informe de Calidad de Código" in prompt


class TestLanguageBackwardCompatibility:
    """Tests para verificar compatibilidad con código existente."""
    
    def test_request_without_language_works(self, tmp_path):
        """El código existente sin language debe seguir funcionando."""
        # Simular request antiguo sin field language
        data = {
            "report_name": "test_report",
            "format": "excel",
            "project_path": str(tmp_path),
            "llm_enabled": True
        }
        
        request = CodeQualityReportRequest.from_dict(data)
        
        # Debe funcionar y usar default
        assert request.language == ReportLanguage.ES_AR
        assert request.llm_enabled is True
    
    def test_request_with_all_original_fields(self, tmp_path):
        """Un request con todos los campos originales debe funcionar."""
        data = {
            "report_name": "test_report",
            "format": "excel",
            "project_path": str(tmp_path),
            "run_id": "test-run-123",
            "llm_enabled": False,
            "include_globs": ["**/*.py"],
            "exclude_globs": ["**/venv/**"],
            "context": {"tech": "auto"}
        }
        
        request = CodeQualityReportRequest.from_dict(data)
        
        # Todos los campos deben estar presentes
        assert request.report_name == "test_report"
        assert request.format == ReportFormat.EXCEL
        assert request.run_id == "test-run-123"
        assert request.llm_enabled is False
        assert request.language == ReportLanguage.ES_AR  # Default
        assert request.include_globs == ["**/*.py"]
        assert request.exclude_globs == ["**/venv/**"]
        assert request.context == {"tech": "auto"}
