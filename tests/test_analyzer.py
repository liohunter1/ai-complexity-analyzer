"""
Unit tests for the RepositoryAnalyzer class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from complexity_analyzer.analyzer import (
    RepositoryAnalyzer,
    OpenAIProvider,
    AnthropicProvider
)
from complexity_analyzer.models import FileComplexity, ComplexityReport


class TestLLMProviders:
    """Test suite for LLM provider classes."""
    
    def test_openai_provider_initialization(self):
        """Test OpenAI provider initializes correctly."""
        provider = OpenAIProvider(model="gpt-4-turbo-preview", temperature=0.1)
        assert provider.llm is not None
        assert provider.parser is not None
    
    def test_anthropic_provider_initialization(self):
        """Test Anthropic provider initializes correctly."""
        provider = AnthropicProvider(model="claude-3-opus-20240229", temperature=0.1)
        assert provider.llm is not None
        assert provider.parser is not None
    
    @patch('complexity_analyzer.analyzer.ChatOpenAI')
    def test_openai_analyze_file(self, mock_llm):
        """Test OpenAI file analysis."""
        # Setup mock
        mock_result = FileComplexity(
            file_path="test.py",
            cyclomatic_complexity=45.0,
            architectural_complexity=60.0,
            algorithmic_complexity=55.0,
            total_score=55.0,
            reasoning="Test reasoning",
            design_patterns=["Factory"]
        )
        
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_result
        
        with patch.object(OpenAIProvider, 'analyze_file', return_value=mock_result):
            provider = OpenAIProvider()
            result = provider.analyze_file("print('hello')", "test.py")
            
            assert result.file_path == "test.py"
            assert result.total_score == 55.0
            assert "Factory" in result.design_patterns


class TestRepositoryAnalyzer:
    """Test suite for RepositoryAnalyzer class."""
    
    def test_analyzer_initialization_openai(self):
        """Test analyzer initializes with OpenAI provider."""
        analyzer = RepositoryAnalyzer(llm_provider="openai")
        assert isinstance(analyzer.llm_provider, OpenAIProvider)
    
    def test_analyzer_initialization_anthropic(self):
        """Test analyzer initializes with Anthropic provider."""
        analyzer = RepositoryAnalyzer(llm_provider="anthropic")
        assert isinstance(analyzer.llm_provider, AnthropicProvider)
    
    def test_analyzer_invalid_provider(self):
        """Test analyzer raises error for invalid provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            RepositoryAnalyzer(llm_provider="invalid")
    
    @patch('complexity_analyzer.analyzer.GitHubAPIClient')
    @patch.object(OpenAIProvider, 'analyze_file')
    def test_analyze_repository(self, mock_analyze, mock_github):
        """Test full repository analysis workflow."""
        # Setup mocks
        mock_github_instance = Mock()
        mock_github_instance.fetch_repository_files.return_value = {
            "src/main.py": "def main(): pass",
            "src/utils.py": "def helper(): pass"
        }
        mock_github.return_value = mock_github_instance
        
        mock_complexity = FileComplexity(
            file_path="src/main.py",
            cyclomatic_complexity=30.0,
            architectural_complexity=40.0,
            algorithmic_complexity=35.0,
            total_score=35.0,
            reasoning="Simple file",
            design_patterns=[]
        )
        mock_analyze.return_value = mock_complexity
        
        # Run analysis
        analyzer = RepositoryAnalyzer(llm_provider="openai")
        analyzer.github_client = mock_github_instance
        
        result = analyzer.analyze("https://github.com/test/repo")
        
        # Verify
        assert isinstance(result, ComplexityReport)
        assert result.repository_url == "https://github.com/test/repo"
        assert len(result.analyzed_files) == 2
        assert result.top_file in ["src/main.py", "src/utils.py"]
    
    def test_exclude_patterns(self):
        """Test file exclusion patterns work correctly."""
        analyzer = RepositoryAnalyzer(
            exclude_patterns=["tests/*", "*.md"]
        )
        assert "tests/*" in analyzer.exclude_patterns
        assert "*.md" in analyzer.exclude_patterns


class TestComplexityReport:
    """Test suite for ComplexityReport model."""
    
    def test_report_creation(self):
        """Test complexity report can be created."""
        file1 = FileComplexity(
            file_path="test1.py",
            cyclomatic_complexity=40.0,
            architectural_complexity=50.0,
            algorithmic_complexity=45.0,
            total_score=45.0,
            reasoning="Test",
            design_patterns=["Singleton"]
        )
        
        report = ComplexityReport(
            repository_url="https://github.com/test/repo",
            analyzed_files=[file1],
            top_file="test1.py",
            score=45.0,
            metadata={"total_files": 1},
            timestamp="2025-12-18T00:00:00Z"
        )
        
        assert report.repository_url == "https://github.com/test/repo"
        assert len(report.analyzed_files) == 1
        assert report.score == 45.0
    
    def test_report_json_serialization(self):
        """Test report can be serialized to JSON."""
        file1 = FileComplexity(
            file_path="test1.py",
            cyclomatic_complexity=40.0,
            architectural_complexity=50.0,
            algorithmic_complexity=45.0,
            total_score=45.0,
            reasoning="Test",
            design_patterns=[]
        )
        
        report = ComplexityReport(
            repository_url="https://github.com/test/repo",
            analyzed_files=[file1],
            top_file="test1.py",
            score=45.0,
            metadata={},
            timestamp="2025-12-18T00:00:00Z"
        )
        
        json_data = report.model_dump()
        assert json_data["repository_url"] == "https://github.com/test/repo"
        assert len(json_data["analyzed_files"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
