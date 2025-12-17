"""
AI Complexity Analyzer - Production-grade code complexity analysis using LLMs.

This package provides tools for analyzing GitHub repositories to identify
technically challenging code patterns using advanced language models.
"""

__version__ = "1.0.0"
__author__ = "NET0HUNTER"

from .analyzer import RepositoryAnalyzer
from .models import ComplexityReport, FileComplexity

__all__ = ["RepositoryAnalyzer", "ComplexityReport", "FileComplexity"]
