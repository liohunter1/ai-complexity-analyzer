"""
Core analyzer implementation using LLM-based complexity evaluation.
"""

import os
from typing import List, Optional, Dict
from abc import ABC, abstractmethod
import logging

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from .models import FileComplexity, ComplexityReport
from .github_client import GitHubAPIClient
from .token_manager import TokenManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers implementing Strategy pattern."""
    
    @abstractmethod
    def analyze_file(self, file_content: str, file_path: str) -> FileComplexity:
        """Analyze a single file for complexity."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider for complexity analysis (default via OPENAI_MODEL)."""
    
    def __init__(self, model: str = "gpt-4-turbo-preview", temperature: float = 0.1):
        chosen_model = model or os.getenv("OPENAI_MODEL", "gpt-5")
        self.llm = ChatOpenAI(
            model=chosen_model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.parser = PydanticOutputParser(pydantic_object=FileComplexity)
        
    def analyze_file(self, file_content: str, file_path: str) -> FileComplexity:
        """Analyze file using GPT-4."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "File: {file_path}\n\nContent:\n{file_content}\n\n{format_instructions}")
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            result = chain.invoke({
                "file_path": file_path,
                "file_content": file_content[:15000],  # Prevent token overflow
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """System prompt for complexity analysis."""
        return """You are an expert software architect analyzing code complexity.

Evaluate the following code file across multiple dimensions:

1. **Cyclomatic Complexity** (0-100): Control flow complexity based on decision points
   - Count if/else, loops, switch statements
   - Nested structures increase score exponentially
   
2. **Architectural Complexity** (0-100): Design pattern sophistication
   - Identify patterns: Factory, Strategy, Observer, Decorator, etc.
   - Assess abstraction layers and dependency injection usage
   
3. **Algorithmic Complexity** (0-100): Algorithm sophistication
   - Analyze time/space complexity (O notation)
   - Identify advanced algorithms (graph traversal, dynamic programming, etc.)

Provide specific reasoning citing line numbers and code constructs.
List all design patterns detected.
Calculate total_score as weighted average: 30% cyclomatic, 40% architectural, 30% algorithmic.

Be precise and evidence-based in your analysis."""


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider for complexity analysis."""
    
    def __init__(self, model: str = "claude-3-opus-20240229", temperature: float = 0.1):
        self.llm = ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.parser = PydanticOutputParser(pydantic_object=FileComplexity)
        
    def analyze_file(self, file_content: str, file_path: str) -> FileComplexity:
        """Analyze file using Claude."""
        # Similar implementation to OpenAI but optimized for Claude's context window
        prompt = ChatPromptTemplate.from_messages([
            ("human", self._get_analysis_prompt(file_path, file_content))
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            result = chain.invoke({
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            raise
    
    def _get_analysis_prompt(self, file_path: str, file_content: str) -> str:
        """Construct analysis prompt for Claude."""
        return f"""Analyze this code file for complexity across multiple dimensions.

File: {file_path}

Content:
{file_content[:20000]}

{self.parser.get_format_instructions()}

Provide detailed complexity analysis with evidence-based reasoning."""


class RepositoryAnalyzer:
    """
    Main analyzer orchestrating the complexity analysis workflow.
    Implements Facade pattern to simplify complex subsystem interactions.
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",
        model: Optional[str] = None,
        max_files: int = 50,
        exclude_patterns: Optional[List[str]] = None,
        complexity_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize the analyzer.
        
        Args:
            llm_provider: "openai" or "anthropic"
            model: Specific model name (defaults to provider's best model)
            max_files: Maximum number of files to analyze
            exclude_patterns: Glob patterns for files to skip
            complexity_weights: Custom weights for complexity components
        """
        self.github_client = GitHubAPIClient()
        self.token_manager = TokenManager()
        self.max_files = max_files
        self.exclude_patterns = exclude_patterns or ["tests/*", "*.md", "*.txt"]
        
        # Factory pattern for LLM provider selection
        self.llm_provider = self._create_llm_provider(llm_provider, model)
        
    def _create_llm_provider(self, provider: str, model: Optional[str]) -> LLMProvider:
        """Factory method for creating LLM providers."""
        if provider == "openai":
            return OpenAIProvider(model=model or os.getenv("OPENAI_MODEL", "gpt-5"))
        elif provider == "anthropic":
            return AnthropicProvider(model=model or "claude-3-opus-20240229")
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def analyze(self, repository_url: str) -> ComplexityReport:
        """
        Analyze a GitHub repository for code complexity.
        
        Args:
            repository_url: Full GitHub repository URL
            
        Returns:
            ComplexityReport with detailed analysis
        """
        logger.info(f"Starting analysis of {repository_url}")
        
        # Fetch repository files
        files = self.github_client.fetch_repository_files(
            repository_url,
            max_files=self.max_files,
            exclude_patterns=self.exclude_patterns
        )
        
        logger.info(f"Analyzing {len(files)} files")
        
        # Analyze each file
        analyzed_files: List[FileComplexity] = []
        for file_path, file_content in files.items():
            try:
                complexity = self.llm_provider.analyze_file(file_content, file_path)
                analyzed_files.append(complexity)
                logger.info(f"✓ {file_path}: {complexity.total_score:.1f}/100")
            except Exception as e:
                logger.warning(f"✗ Failed to analyze {file_path}: {e}")
                continue
        
        # Determine top file and overall score
        top_file = max(analyzed_files, key=lambda x: x.total_score)
        avg_score = sum(f.total_score for f in analyzed_files) / len(analyzed_files)
        
        return ComplexityReport(
            repository_url=repository_url,
            analyzed_files=analyzed_files,
            top_file=top_file.file_path,
            score=round(avg_score, 2),
            metadata={
                "total_files": len(files),
                "analyzed_count": len(analyzed_files),
                "excluded_patterns": self.exclude_patterns
            },
            timestamp=self._get_timestamp()
        )
    
    def _get_timestamp(self) -> str:
        """Get ISO format timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
