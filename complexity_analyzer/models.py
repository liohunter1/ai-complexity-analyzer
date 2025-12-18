"""
Data models for complexity analysis using Pydantic for validation.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class ComplexityCategory(str, Enum):
    """Categories of code complexity analysis."""
    CYCLOMATIC = "cyclomatic"
    ARCHITECTURAL = "architectural"
    ALGORITHMIC = "algorithmic"
    DEPENDENCY = "dependency"


class FileComplexity(BaseModel):
    """Complexity analysis for a single file."""
    
    file_path: str = Field(..., description="Relative path to file in repository")
    total_score: float = Field(..., ge=0, le=100, description="Overall complexity score (0-100)")
    
    cyclomatic_score: float = Field(..., ge=0, le=100)
    architectural_score: float = Field(..., ge=0, le=100)
    algorithmic_score: float = Field(..., ge=0, le=100)
    
    line_count: int = Field(..., gt=0)
    function_count: int = Field(..., ge=0)
    class_count: int = Field(..., ge=0)
    
    patterns_detected: List[str] = Field(default_factory=list)
    reasoning: str = Field(..., min_length=10)
    
    @validator('total_score')
    def validate_total_score(cls, v: float, values: Dict) -> float:
        """Ensure total score is reasonable given component scores."""
        if 'cyclomatic_score' in values and 'architectural_score' in values:
            # Basic sanity check - total should be in range of components
            min_score = min(values.get('cyclomatic_score', 0), 
                          values.get('architectural_score', 0))
            if v < min_score - 20:  # Allow some variance
                raise ValueError("Total score significantly below component scores")
        return v


class ComplexityReport(BaseModel):
    """Complete complexity analysis report for a repository."""
    
    repository_url: str
    analyzed_files: List[FileComplexity]
    top_file: str = Field(..., description="Most complex file in repository")
    score: float = Field(..., ge=0, le=100, description="Repository-wide complexity score")
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str
    
    @validator('top_file')
    def validate_top_file(cls, v: str, values: Dict) -> str:
        """Ensure top_file exists in analyzed_files."""
        if 'analyzed_files' in values:
            file_paths = [f.file_path for f in values['analyzed_files']]
            if v not in file_paths:
                raise ValueError(f"Top file {v} not found in analyzed files")
        return v
    
    def get_files_by_complexity(self, threshold: float = 70.0) -> List[FileComplexity]:
        """Return files exceeding complexity threshold."""
        return sorted(
            [f for f in self.analyzed_files if f.total_score >= threshold],
            key=lambda x: x.total_score,
            reverse=True
        )
    
    def get_pattern_distribution(self) -> Dict[str, int]:
        """Count occurrences of each design pattern across all files."""
        pattern_counts: Dict[str, int] = {}
        for file in self.analyzed_files:
            for pattern in file.patterns_detected:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        return dict(sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True))
