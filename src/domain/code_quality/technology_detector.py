"""Technology detection for code quality analysis."""

from pathlib import Path
import logging

from .enums import ProjectTechnology

logger = logging.getLogger(__name__)


class TechnologyDetector:
    """Detects project technology based on filesystem markers."""
    
    def detect(self, project_path: str) -> ProjectTechnology:
        """
        Detect the technology of a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            ProjectTechnology enum value
        """
        path = Path(project_path)
        
        # Detect Spring Boot
        if self._is_spring_boot(path):
            logger.info(f"Detected Spring Boot project at {project_path}")
            return ProjectTechnology.SPRING_BOOT
        
        # Detect Angular
        if self._is_angular(path):
            logger.info(f"Detected Angular project at {project_path}")
            return ProjectTechnology.ANGULAR
        
        # Detect Python
        if self._is_python(path):
            logger.info(f"Detected Python project at {project_path}")
            return ProjectTechnology.PYTHON
        
        logger.warning(f"Could not detect technology for project at {project_path}")
        return ProjectTechnology.UNKNOWN
    
    def _is_spring_boot(self, path: Path) -> bool:
        """Check if project is Spring Boot."""
        has_maven = (path / "pom.xml").exists()
        has_gradle = (path / "build.gradle").exists() or (path / "build.gradle.kts").exists()
        has_java_src = (path / "src" / "main" / "java").exists()
        
        return (has_maven or has_gradle) and has_java_src
    
    def _is_angular(self, path: Path) -> bool:
        """Check if project is Angular."""
        has_package_json = (path / "package.json").exists()
        has_angular_json = (path / "angular.json").exists()
        
        return has_package_json and has_angular_json
    
    def _is_python(self, path: Path) -> bool:
        """Check if project is Python."""
        has_requirements = (path / "requirements.txt").exists()
        has_pyproject = (path / "pyproject.toml").exists()
        has_setup_py = (path / "setup.py").exists()
        
        # Check for .py files in root or src
        has_py_files = (
            any(path.glob("*.py")) or 
            (path / "src").exists() and any((path / "src").rglob("*.py"))
        )
        
        return (has_requirements or has_pyproject or has_setup_py) or has_py_files
