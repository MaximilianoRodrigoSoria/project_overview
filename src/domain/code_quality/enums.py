"""Enums for code quality domain."""

from enum import Enum


class ProjectTechnology(str, Enum):
    """Supported project technologies for code quality analysis."""
    
    SPRING_BOOT = "spring_boot"
    ANGULAR = "angular"
    PYTHON = "python"
    UNKNOWN = "unknown"
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a value is valid for this enum."""
        if not value:
            return False
        try:
            cls(value.lower())
            return True
        except ValueError:
            return False
    
    @classmethod
    def values(cls) -> list:
        """Return all valid values."""
        return [tech.value for tech in cls if tech != cls.UNKNOWN]


class ReportLanguage(str, Enum):
    """Supported languages for LLM narrative generation."""
    
    ES_AR = "es-AR"
    ES = "es"
    EN = "en"
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a value is valid for this enum."""
        if not value:
            return False
        try:
            cls(value)
            return True
        except ValueError:
            return False
    
    @classmethod
    def values(cls) -> list:
        """Return all valid values."""
        return [lang.value for lang in cls]
    
    @classmethod
    def default(cls) -> "ReportLanguage":
        """Return default language."""
        return cls.ES_AR
