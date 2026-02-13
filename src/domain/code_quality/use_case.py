"""Use case for code quality report generation."""

import json
import logging
from typing import Optional

from ...ports.llm_port import LLMPort
from ..reporting.exceptions import ValidationError
from .dtos import (
    CodeQualityReportRequest,
    CodeQualityReportResult,
    CodeQualityMetrics,
    CodeQualityNarrative
)
from .enums import ProjectTechnology, ReportLanguage
from .technology_detector import TechnologyDetector
from .analyzers import AnalyzerFactory

logger = logging.getLogger(__name__)


class GenerateCodeQualityReportUseCase:
    """Use case for generating code quality reports."""
    
    def __init__(self, llm: Optional[LLMPort] = None):
        """
        Initialize use case.
        
        Args:
            llm: LLM port for narrative generation (optional)
        """
        self.llm = llm
        self.detector = TechnologyDetector()
    
    def execute(self, request: CodeQualityReportRequest) -> CodeQualityReportResult:
        """
        Execute code quality report generation.
        
        Args:
            request: Code quality report request
            
        Returns:
            CodeQualityReportResult with metrics and optional narrative
            
        Raises:
            ValidationError: If technology cannot be detected or analysis fails
        """
        run_id = request.run_id
        
        logger.info(f"[{run_id}] Starting code quality analysis for: {request.project_path}")
        
        # Step 1: Detect technology
        technology = self.detector.detect(request.project_path)
        
        if technology == ProjectTechnology.UNKNOWN:
            raise ValidationError(
                f"Could not detect technology for project at: {request.project_path}. "
                f"Supported: Spring Boot, Angular, Python"
            )
        
        logger.info(f"[{run_id}] Detected technology: {technology.value}")
        
        # Step 2: Get appropriate analyzer
        analyzer = AnalyzerFactory.get_analyzer(technology)
        
        # Step 3: Perform deterministic analysis
        logger.info(f"[{run_id}] Performing deterministic analysis...")
        analysis_result = analyzer.analyze(
            request.project_path,
            request.include_globs or [],
            request.exclude_globs or []
        )
        
        # Step 4: Build metrics
        metrics = CodeQualityMetrics(
            total_files=analysis_result["total_files"],
            total_lines=analysis_result["total_lines"],
            avg_lines_per_file=analysis_result["avg_lines_per_file"],
            technology=technology,
            tech_metrics=analysis_result.get("tech_metrics", {})
        )
        
        logger.info(
            f"[{run_id}] Analysis complete: {metrics.total_files} files, "
            f"{metrics.total_lines} lines, tech={technology.value}"
        )
        
        # Step 5: Generate narrative if requested
        narrative = None
        if request.llm_enabled:
            logger.info(f"[{run_id}] Generating LLM narrative in {request.language.value}...")
            narrative = self._generate_narrative(run_id, technology, metrics, request.language)
        
        # Step 6: Build result
        result = CodeQualityReportResult(
            run_id=run_id,
            report_name=request.report_name,
            format=request.format,
            project_path=request.project_path,
            metrics=metrics,
            narrative=narrative
        )
        
        logger.info(f"[{run_id}] Code quality report generated successfully")
        
        return result
    
    def _generate_narrative(
        self,
        run_id: str,
        technology: ProjectTechnology,
        metrics: CodeQualityMetrics,
        language: ReportLanguage
    ) -> Optional[CodeQualityNarrative]:
        """
        Generate narrative using LLM.
        
        Args:
            run_id: Run ID for logging
            technology: Detected technology
            metrics: Analysis metrics
            language: Language for narrative generation
            
        Returns:
            CodeQualityNarrative or None if LLM fails
        """
        if self.llm is None:
            logger.warning(f"[{run_id}] LLM not configured, skipping narrative")
            return None
        
        try:
            # Build prompt with language instruction
            prompt = self._build_llm_prompt(technology, metrics, language)
            
            # Build system prompt with language instruction
            system_prompt = self._build_system_prompt(language)
            
            narrative_text = self.llm.generate_text(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # Parse narrative (simple split by sections)
            recommendations = self._extract_recommendations(narrative_text)
            insights = self._extract_insights(narrative_text)
            
            # Store the complete narrative - DO NOT TRUNCATE
            # The full LLM-generated report should be preserved
            return CodeQualityNarrative(
                summary=narrative_text,  # Full narrative, not truncated
                recommendations=recommendations,
                insights=insights
            )
            
        except Exception as e:
            logger.error(f"[{run_id}] Error generating narrative: {e}", exc_info=True)
            return None
    
    def _build_system_prompt(self, language: ReportLanguage) -> str:
        """Build system prompt with language instruction."""
        
        if language == ReportLanguage.ES_AR or language == ReportLanguage.ES:
            base_prompt = (
                "Sos un Arquitecto de Software Senior con amplia experiencia en análisis de calidad de código, "
                "patrones de diseño y mejores prácticas de desarrollo. "
                "Tu rol es analizar métricas técnicas y generar informes profesionales con insights accionables."
            )
            language_instruction = (
                "\n\nREGLAS ESTRICTAS:\n"
                "- Generá el informe en Español (Argentina) con tono profesional técnico\n"
                "- No uses frases genéricas como 'podría beneficiarse' o 'se recomienda'\n"
                "- No repitas las métricas numéricas que ya están en los datos\n"
                "- No uses introducciones conversacionales\n"
                "- No truncues el contenido\n"
                "- No inventes datos o métricas\n"
                "- Mantené el foco en análisis técnico profundo\n"
                "- Usá terminología técnica precisa\n"
                "- No traduzcas nombres de tecnologías (Spring Boot, Angular, Python, etc.)"
            )
        elif language == ReportLanguage.EN:
            base_prompt = (
                "You are a Senior Software Architect with extensive experience in code quality analysis, "
                "design patterns, and development best practices. "
                "Your role is to analyze technical metrics and generate professional reports with actionable insights."
            )
            language_instruction = (
                "\n\nSTRICT RULES:\n"
                "- Generate the report in professional technical English\n"
                "- Avoid generic phrases like 'could benefit from' or 'it is recommended'\n"
                "- Do not repeat numerical metrics already in the data\n"
                "- Do not use conversational introductions\n"
                "- Do not truncate content\n"
                "- Do not invent data or metrics\n"
                "- Maintain focus on deep technical analysis\n"
                "- Use precise technical terminology"
            )
        else:
            # Default to Spanish Argentina
            base_prompt = (
                "Sos un Arquitecto de Software Senior con amplia experiencia en análisis de calidad de código."
            )
            language_instruction = "\n\nGenerá el informe en Español (Argentina) con tono profesional técnico."
        
        return base_prompt + language_instruction
    
    def _build_llm_prompt(
        self,
        technology: ProjectTechnology,
        metrics: CodeQualityMetrics,
        language: ReportLanguage
    ) -> str:
        """Build LLM prompt from metrics with language instruction."""
        
        metrics_dict = {
            "technology": technology.value,
            "total_files": metrics.total_files,
            "total_lines": metrics.total_lines,
            "avg_lines_per_file": metrics.avg_lines_per_file,
            "tech_specific_metrics": metrics.tech_metrics
        }
        
        metrics_json = json.dumps(metrics_dict, indent=2)
        
        # Build prompt in appropriate language
        if language in (ReportLanguage.ES_AR, ReportLanguage.ES):
            # Extract tech-specific metrics
            tech_specific = ""
            tech_context = ""
            
            if technology == ProjectTechnology.SPRING_BOOT:
                num_classes = metrics.tech_metrics.get("num_classes", 0)
                controllers = metrics.tech_metrics.get("num_rest_controllers", 0)
                services = metrics.tech_metrics.get("num_services", 0)
                repositories = metrics.tech_metrics.get("num_repositories", 0)
                tech_specific = f"""
Clases: {num_classes}
Controladores REST: {controllers}
Servicios: {services}
Repositorios: {repositories}"""
                tech_context = "aplicación Spring Boot con arquitectura en capas (Controllers, Services, Repositories)"
                
            elif technology == ProjectTechnology.ANGULAR:
                components = metrics.tech_metrics.get("num_components", 0)
                services = metrics.tech_metrics.get("num_services", 0)
                estimated_kb = metrics.tech_metrics.get("estimated_bundle_size_kb", 0)
                tech_specific = f"""
Componentes: {components}
Servicios: {services}
Tamaño estimado del bundle: {estimated_kb} KB"""
                tech_context = "aplicación Angular con arquitectura de componentes y servicios"
                
            elif technology == ProjectTechnology.PYTHON:
                modules = metrics.tech_metrics.get("num_modules", 0)
                functions = metrics.tech_metrics.get("num_functions", 0)
                classes = metrics.tech_metrics.get("num_classes", 0)
                tech_specific = f"""
Módulos: {modules}
Funciones: {functions}
Clases: {classes}"""
                tech_context = "proyecto Python con estructura modular"
            
            prompt = f"""Actuá como Arquitecto de Software Senior.

Este no es un chat interactivo.
No hagas preguntas.
No pidas información adicional.
No solicites métricas.
No hagas aclaraciones.
Debés generar el informe directamente usando los datos proporcionados.

Los siguientes datos ya fueron calculados y son correctos:

Tecnología: {technology.value}
Total archivos: {metrics.total_files}
Total líneas: {metrics.total_lines}
Promedio líneas por archivo: {metrics.avg_lines_per_file:.1f}{tech_specific}

Generá un informe técnico profesional en Español (Argentina).

Reglas estrictas:
- No preguntar nada.
- No repetir métricas numéricamente en el texto.
- No usar frases genéricas del tipo "podría beneficiarse" o "se recomienda considerar".
- No inventar datos.
- No usar tono conversacional.
- No usar introducciones del tipo "Hola" o "A continuación".
- No pedir información adicional.
- No truncar el texto.
- Interpretar las métricas técnicamente, no solo listarlas.
- Emitir análisis profundo basado en patrones arquitectónicos y mejores prácticas.

Estructura obligatoria:

# Informe Técnico de Calidad de Código

## Diagnóstico Estructural
Realizá un análisis técnico interpretando:
- El tamaño del proyecto ({metrics.total_files} archivos, {metrics.total_lines} líneas) en el contexto de una {tech_context}
- El promedio de líneas por archivo y su relación con mantenibilidad (rango óptimo 50-200 líneas)
- La distribución de componentes y su balance arquitectónico
- Indicadores de complejidad estructural derivados de las métricas

## Análisis de Capas
Evaluá la arquitectura de capas/componentes basado en las métricas específicas:
- Distribución y proporción de componentes por capa
- Indicadores de cohesión y acoplamiento potencial
- Patrones arquitectónicos evidentes (si aplica según tecnología)
- Balance entre abstracciones e implementaciones concretas

## Riesgos Arquitectónicos
Identificá riesgos técnicos específicos basados en:
- Archivos que excedan significativamente el promedio (indicadores de complejidad concentrada)
- Desbalance en la distribución de responsabilidades entre capas/componentes
- Patrones que sugieran alto acoplamiento o baja cohesión
- Señales de código duplicado o falta de abstracción
- Puntos de mantenibilidad comprometida

## Recomendaciones Técnicas
Proporcioná recomendaciones concretas y accionables:
- Refactorizaciones específicas con patrones de diseño aplicables (Strategy, Factory, etc.)
- Segregación de responsabilidades con técnicas concretas (SOLID, DRY, KISS)
- Mejoras en la estructura de capas/módulos
- Optimizaciones de mantenibilidad con acciones específicas
- Herramientas o prácticas técnicas aplicables al contexto ({technology.value})

Cada recomendación debe incluir QUÉ hacer y CÓMO implementarlo técnicamente."""
        else:  # EN
            prompt = f"""
Analyze the following code quality metrics for a {technology.value} project:

{metrics_json}

Please provide:
1. A brief summary of the project's code quality
2. Key insights about the codebase structure
3. Specific recommendations for improvement
4. Potential code quality concerns

Focus on actionable technical recommendations based on the metrics.
"""
        
        return prompt
    
    def _extract_recommendations(self, narrative: str) -> list:
        """Extract recommendations from narrative text."""
        # Simple extraction - look for numbered lists or bullet points
        recommendations = []
        lines = narrative.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (
                line.startswith('- ') or 
                line.startswith('* ') or 
                (len(line) > 2 and line[0].isdigit() and line[1] in '.)')
            ):
                # Remove bullet/number
                rec = line.lstrip('- *0123456789.)')
                if rec and len(rec) > 10:  # Minimum length
                    recommendations.append(rec.strip())
        
        return recommendations[:5]  # Limit to top 5
    
    def _extract_insights(self, narrative: str) -> list:
        """Extract insights from narrative text."""
        # Similar to recommendations but look for different patterns
        insights = []
        lines = narrative.split('\n')
        
        for line in lines:
            line = line.strip()
            if 'insight' in line.lower() or 'note' in line.lower():
                if len(line) > 20:
                    insights.append(line)
        
        return insights[:3]  # Limit to top 3
    
    @staticmethod
    def to_writer_payload(result: CodeQualityReportResult) -> dict:
        """
        Convert result to payload for writers.
        
        Args:
            result: Code quality report result
            
        Returns:
            Dictionary formatted for report writers
        """
        payload = {
            "report_name": result.report_name,
            "project_path": result.project_path,
            "technology": result.metrics.technology.value,
            "metrics": {
                "total_files": result.metrics.total_files,
                "total_lines": result.metrics.total_lines,
                "avg_lines_per_file": result.metrics.avg_lines_per_file,
                **result.metrics.tech_metrics
            }
        }
        
        if result.narrative:
            payload["narrative"] = {
                "summary": result.narrative.summary,
                "recommendations": result.narrative.recommendations,
                "insights": result.narrative.insights
            }
        
        return payload
