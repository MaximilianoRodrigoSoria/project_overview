"""DTOs for code quality domain."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path

from ..reporting.enums import ReportFormat
from ..reporting.exceptions import ValidationError
from ..reporting.utils import generate_run_id, validate_run_id
from .enums import ProjectTechnology, ReportLanguage


@dataclass
class CodeQualityReportRequest:
    """Input payload for code quality report generation."""
    
    report_name: str
    format: ReportFormat
    project_path: str
    run_id: Optional[str] = None
    llm_enabled: bool = False
    language: ReportLanguage = ReportLanguage.ES_AR
    include_globs: Optional[List[str]] = None
    exclude_globs: Optional[List[str]] = None
    context: Optional[Dict[str, str]] = None
    
    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        
        # Validate required fields
        if not self.report_name or not self.report_name.strip():
            raise ValidationError("Missing required field: report_name")
        
        if not self.project_path or not self.project_path.strip():
            raise ValidationError("Missing required field: project_path")
        
        # Validate project_path exists
        path = Path(self.project_path)
        if not path.exists():
            raise ValidationError(f"Project path does not exist: {self.project_path}")
        
        if not path.is_dir():
            raise ValidationError(f"Project path must be a directory: {self.project_path}")
        
        # Validate format
        if not isinstance(self.format, ReportFormat):
            raise ValidationError(f"Invalid format: {self.format}")
        
        # Validate language
        if not isinstance(self.language, ReportLanguage):
            # Si language viene como string, intentar convertirlo
            if isinstance(self.language, str):
                if not ReportLanguage.is_valid(self.language):
                    raise ValidationError(
                        f"Invalid language: {self.language}. "
                        f"Allowed values: {', '.join(ReportLanguage.values())}"
                    )
                self.language = ReportLanguage(self.language)
            else:
                raise ValidationError(f"Invalid language type: {type(self.language)}")
        
        # Generate run_id if not provided
        if self.run_id:
            validate_run_id(self.run_id)
        else:
            self.run_id = generate_run_id()
        
        # Set defaults
        if self.include_globs is None:
            self.include_globs = []
        
        if self.exclude_globs is None:
            self.exclude_globs = [
                "**/target/**",
                "**/node_modules/**",
                "**/dist/**",
                "**/__pycache__/**",
                "**/.venv/**",
                "**/venv/**",
                "**/.git/**"
            ]
        
        if self.context is None:
            self.context = {"tech": "auto"}
        
        # Validate context structure
        if not isinstance(self.context, dict):
            raise ValidationError("Field 'context' must be an object")
        
        allowed_keys = {"tech"}
        invalid_keys = set(self.context.keys()) - allowed_keys
        if invalid_keys:
            raise ValidationError(
                f"Invalid properties in context: {', '.join(invalid_keys)}. "
                f"Allowed: {', '.join(allowed_keys)}"
            )
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "CodeQualityReportRequest":
        """Create instance from dictionary."""
        
        # Validate required fields
        required_fields = ["report_name", "format", "project_path"]
        missing = [
            field for field in required_fields
            if field not in data or data[field] in (None, "")
        ]
        
        if missing:
            raise ValidationError(
                f"Missing required field(s): {', '.join(missing)}"
            )
        
        # Validate format
        format_value = str(data.get("format", "")).lower()
        if not ReportFormat.is_valid(format_value):
            from ..reporting.exceptions import InvalidFormatError
            raise InvalidFormatError(f"Format not supported: {format_value}")
        
        # Validate language (optional, default es-AR)
        language_value = data.get("language", "es-AR")
        if language_value and not ReportLanguage.is_valid(language_value):
            raise ValidationError(
                f"Invalid language: {language_value}. "
                f"Allowed values: {', '.join(ReportLanguage.values())}"
            )
        
        language = ReportLanguage(language_value) if language_value else ReportLanguage.default()
        
        return cls(
            report_name=str(data["report_name"]),
            format=ReportFormat(format_value),
            project_path=str(data["project_path"]),
            run_id=data.get("run_id"),
            llm_enabled=bool(data.get("llm_enabled", False)),
            language=language,
            include_globs=data.get("include_globs"),
            exclude_globs=data.get("exclude_globs"),
            context=data.get("context")
        )


@dataclass
class CodeQualityMetrics:
    """Deterministic code quality metrics."""
    
    # General metrics
    total_files: int
    total_lines: int
    avg_lines_per_file: float
    technology: ProjectTechnology
    
    # Technology-specific metrics
    tech_metrics: Dict[str, object] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate metrics."""
        if self.total_files < 0:
            raise ValidationError("total_files must be non-negative")
        
        if self.total_lines < 0:
            raise ValidationError("total_lines must be non-negative")
        
        if self.avg_lines_per_file < 0:
            raise ValidationError("avg_lines_per_file must be non-negative")


@dataclass
class CodeQualityNarrative:
    """Optional LLM-generated narrative."""
    
    summary: str
    recommendations: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)


@dataclass
class CodeQualityReportResult:
    """Final report result before rendering."""
    
    run_id: str
    report_name: str
    format: ReportFormat
    project_path: str
    metrics: CodeQualityMetrics
    narrative: Optional[CodeQualityNarrative] = None
