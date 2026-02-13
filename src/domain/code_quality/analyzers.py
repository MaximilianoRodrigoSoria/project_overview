"""Code analyzers for different technologies."""

import re
from pathlib import Path
from typing import Dict, List
import logging

from .enums import ProjectTechnology

logger = logging.getLogger(__name__)


class BaseAnalyzer:
    """Base analyzer with common functionality."""
    
    def count_lines_in_file(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return 0
    
    def read_file_content(self, file_path: Path) -> str:
        """Read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return ""
    
    def should_exclude(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if file should be excluded based on patterns."""
        file_str = str(file_path)
        for pattern in exclude_patterns:
            # Simple pattern matching
            pattern_clean = pattern.replace("**/", "").replace("/**", "").replace("*", "")
            if pattern_clean in file_str:
                return True
        return False


class SpringBootAnalyzer(BaseAnalyzer):
    """Analyzer for Spring Boot projects."""
    
    def analyze(self, project_path: str, include_globs: List[str], exclude_globs: List[str]) -> Dict[str, object]:
        """
        Analyze a Spring Boot project.
        
        Returns:
            Dictionary with metrics
        """
        path = Path(project_path)
        
        # Find Java files
        java_files = list(path.rglob("*.java"))
        java_files = [f for f in java_files if not self.should_exclude(f, exclude_globs)]
        
        total_files = len(java_files)
        total_lines = sum(self.count_lines_in_file(f) for f in java_files)
        avg_lines = total_lines / total_files if total_files > 0 else 0
        
        # Count specific patterns
        num_classes = 0
        num_rest_controllers = 0
        num_services = 0
        num_repositories = 0
        
        for java_file in java_files:
            content = self.read_file_content(java_file)
            
            # Count classes
            num_classes += len(re.findall(r'\bclass\s+\w+', content))
            
            # Count Spring annotations
            num_rest_controllers += len(re.findall(r'@RestController', content))
            num_services += len(re.findall(r'@Service', content))
            num_repositories += len(re.findall(r'@Repository', content))
        
        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "avg_lines_per_file": round(avg_lines, 2),
            "tech_metrics": {
                "num_classes": num_classes,
                "num_rest_controllers": num_rest_controllers,
                "num_services": num_services,
                "num_repositories": num_repositories
            }
        }


class AngularAnalyzer(BaseAnalyzer):
    """Analyzer for Angular projects."""
    
    def analyze(self, project_path: str, include_globs: List[str], exclude_globs: List[str]) -> Dict[str, object]:
        """
        Analyze an Angular project.
        
        Returns:
            Dictionary with metrics
        """
        path = Path(project_path)
        
        # Find TypeScript files
        ts_files = list(path.rglob("*.ts"))
        ts_files = [f for f in ts_files if not self.should_exclude(f, exclude_globs)]
        
        total_files = len(ts_files)
        total_lines = sum(self.count_lines_in_file(f) for f in ts_files)
        avg_lines = total_lines / total_files if total_files > 0 else 0
        
        # Count specific patterns
        num_components = 0
        num_services = 0
        
        for ts_file in ts_files:
            file_name = ts_file.name
            
            if file_name.endswith(".component.ts"):
                num_components += 1
            elif file_name.endswith(".service.ts"):
                num_services += 1
        
        # Estimate bundle size (rough approximation)
        estimated_bundle_size_kb = round(total_lines * 0.05, 2)  # 50 bytes per line average
        
        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "avg_lines_per_file": round(avg_lines, 2),
            "tech_metrics": {
                "num_components": num_components,
                "num_services": num_services,
                "estimated_bundle_size_kb": estimated_bundle_size_kb
            }
        }


class PythonAnalyzer(BaseAnalyzer):
    """Analyzer for Python projects."""
    
    def analyze(self, project_path: str, include_globs: List[str], exclude_globs: List[str]) -> Dict[str, object]:
        """
        Analyze a Python project.
        
        Returns:
            Dictionary with metrics
        """
        path = Path(project_path)
        
        # Find Python files
        py_files = list(path.rglob("*.py"))
        py_files = [f for f in py_files if not self.should_exclude(f, exclude_globs)]
        
        total_files = len(py_files)
        total_lines = sum(self.count_lines_in_file(f) for f in py_files)
        avg_lines = total_lines / total_files if total_files > 0 else 0
        
        # Count specific patterns
        num_modules = total_files  # Each .py file is a module
        num_functions = 0
        num_classes = 0
        
        for py_file in py_files:
            content = self.read_file_content(py_file)
            
            # Count functions (def keyword)
            num_functions += len(re.findall(r'\ndef\s+\w+', content))
            
            # Count classes
            num_classes += len(re.findall(r'\nclass\s+\w+', content))
        
        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "avg_lines_per_file": round(avg_lines, 2),
            "tech_metrics": {
                "num_modules": num_modules,
                "num_functions": num_functions,
                "num_classes": num_classes
            }
        }


class AnalyzerFactory:
    """Factory to get the appropriate analyzer for a technology."""
    
    @staticmethod
    def get_analyzer(technology: ProjectTechnology) -> BaseAnalyzer:
        """Get analyzer for given technology."""
        analyzers = {
            ProjectTechnology.SPRING_BOOT: SpringBootAnalyzer(),
            ProjectTechnology.ANGULAR: AngularAnalyzer(),
            ProjectTechnology.PYTHON: PythonAnalyzer()
        }
        
        analyzer = analyzers.get(technology)
        if analyzer is None:
            from ..reporting.exceptions import ValidationError
            raise ValidationError(f"No analyzer available for technology: {technology.value}")
        
        return analyzer
