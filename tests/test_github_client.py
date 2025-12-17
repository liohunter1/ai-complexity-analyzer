"""
Unit tests for GitHub API client.
"""

import pytest
from unittest.mock import Mock, patch
from complexity_analyzer.github_client import GitHubAPIClient


class TestGitHubAPIClient:
    """Test suite for GitHubAPIClient."""
    
    def test_parse_repo_url_https(self):
        """Test parsing HTTPS GitHub URLs."""
        client = GitHubAPIClient()
        
        owner, repo = client.parse_repo_url("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_parse_repo_url_git(self):
        """Test parsing .git URLs."""
        client = GitHubAPIClient()
        
        owner, repo = client.parse_repo_url("https://github.com/owner/repo.git")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_parse_repo_url_invalid(self):
        """Test parsing invalid URLs raises error."""
        client = GitHubAPIClient()
        
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            client.parse_repo_url("https://example.com/invalid")
    
    @patch('requests.Session.get')
    def test_get_repo_tree(self, mock_get):
        """Test fetching repository tree."""
        client = GitHubAPIClient()
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tree": [
                {"type": "blob", "path": "test.py"},
                {"type": "tree", "path": "src"}
            ]
        }
        mock_get.return_value = mock_response
        
        tree = client._get_repo_tree("owner", "repo")
        
        assert len(tree) == 2
        assert tree[0]["path"] == "test.py"
    
    def test_filter_code_files(self):
        """Test filtering code files from tree."""
        client = GitHubAPIClient()
        
        tree = [
            {"type": "blob", "path": "src/main.py"},
            {"type": "blob", "path": "README.md"},
            {"type": "blob", "path": "tests/test_main.py"},
            {"type": "tree", "path": "docs"}
        ]
        
        code_files = client._filter_code_files(
            tree,
            exclude_patterns=["tests/*", "*.md"]
        )
        
        assert len(code_files) == 1
        assert "src/main.py" in code_files
    
    def test_should_exclude(self):
        """Test exclude pattern matching."""
        client = GitHubAPIClient()
        
        assert client._should_exclude("tests/test.py", ["tests/*"]) is True
        assert client._should_exclude("src/main.py", ["tests/*"]) is False
        assert client._should_exclude("README.md", ["*.md"]) is True
    
    @patch('requests.Session.get')
    def test_get_file_content(self, mock_get):
        """Test fetching file content."""
        import base64
        
        client = GitHubAPIClient()
        
        # Mock response
        content = "print('hello world')"
        encoded = base64.b64encode(content.encode()).decode()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": encoded}
        mock_get.return_value = mock_response
        
        result = client._get_file_content("owner", "repo", "test.py")
        
        assert result == content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
