"""
GitHub API client with rate limiting and error handling.
"""

import os
import re
from typing import Dict, List, Optional
import requests
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """
    Client for interacting with GitHub API.
    Implements Repository pattern for data access.
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (or uses GITHUB_TOKEN env var)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
    
    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """
        Parse GitHub URL to extract owner and repo name.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Tuple of (owner, repo_name)
        """
        # Support various URL formats
        patterns = [
            r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$",
            r"github\.com/([^/]+)/([^/]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2).rstrip(".git")
        
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    def fetch_repository_files(
        self,
        repository_url: str,
        max_files: int = 50,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Fetch all code files from a repository.
        
        Args:
            repository_url: GitHub repository URL
            max_files: Maximum number of files to fetch
            exclude_patterns: List of glob patterns to exclude
            
        Returns:
            Dictionary mapping file paths to file contents
        """
        owner, repo = self.parse_repo_url(repository_url)
        exclude_patterns = exclude_patterns or []
        
        logger.info(f"Fetching files from {owner}/{repo}")
        
        # Get repository tree
        tree = self._get_repo_tree(owner, repo)
        
        # Filter code files
        code_files = self._filter_code_files(tree, exclude_patterns)
        
        # Limit to max_files
        code_files = code_files[:max_files]
        
        # Fetch file contents
        file_contents = {}
        for file_path in code_files:
            try:
                content = self._get_file_content(owner, repo, file_path)
                file_contents[file_path] = content
                logger.debug(f"Fetched {file_path} ({len(content)} bytes)")
            except Exception as e:
                logger.warning(f"Failed to fetch {file_path}: {e}")
                continue
        
        return file_contents
    
    def _get_repo_tree(self, owner: str, repo: str) -> List[Dict]:
        """Get repository tree (list of all files)."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/main?recursive=1"
        
        # Try 'main' branch first, fallback to 'master'
        response = self.session.get(url)
        
        if response.status_code == 404:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/master?recursive=1"
            response = self.session.get(url)
        
        response.raise_for_status()
        data = response.json()
        
        return data.get("tree", [])
    
    def _filter_code_files(
        self,
        tree: List[Dict],
        exclude_patterns: List[str]
    ) -> List[str]:
        """Filter tree to only include code files."""
        code_extensions = {
            ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".hpp",
            ".go", ".rs", ".rb", ".php", ".cs", ".swift", ".kt", ".scala"
        }
        
        code_files = []
        
        for item in tree:
            if item["type"] != "blob":
                continue
            
            path = item["path"]
            
            # Check extension
            if not any(path.endswith(ext) for ext in code_extensions):
                continue
            
            # Check exclude patterns
            if self._should_exclude(path, exclude_patterns):
                continue
            
            code_files.append(path)
        
        return code_files
    
    def _should_exclude(self, path: str, patterns: List[str]) -> bool:
        """Check if path matches any exclude pattern."""
        from fnmatch import fnmatch
        
        for pattern in patterns:
            if fnmatch(path, pattern):
                return True
        
        return False
    
    def _get_file_content(self, owner: str, repo: str, file_path: str) -> str:
        """Get content of a specific file."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        # Decode base64 content
        import base64
        content = base64.b64decode(data["content"]).decode("utf-8")
        
        return content
    
    def get_rate_limit(self) -> Dict:
        """Check current API rate limit status."""
        url = f"{self.BASE_URL}/rate_limit"
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
