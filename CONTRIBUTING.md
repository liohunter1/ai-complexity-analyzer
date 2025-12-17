# Contributing to AI Complexity Analyzer

Thank you for considering contributing to this project! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, professional, and constructive in all interactions.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-complexity-analyzer.git
   cd ai-complexity-analyzer
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set Up Pre-Commit Hooks** (Optional)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write clean, documented code
   - Follow existing code style (Black + Ruff)
   - Add type hints
   - Include docstrings

3. **Write Tests**
   - All new code must have tests
   - Maintain >80% coverage
   - Run tests: `pytest`

4. **Lint and Format**
   ```bash
   black .
   ruff check . --fix
   mypy complexity_analyzer
   ```

5. **Commit with Conventional Commits**
   ```bash
   git commit -m "feat: add new analysis metric"
   git commit -m "fix: resolve token overflow issue"
   git commit -m "docs: update README examples"
   ```

   Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Guidelines

- **Title**: Use conventional commit format
- **Description**: Explain what and why, not how
- **Tests**: Include test coverage
- **Documentation**: Update README if needed
- **Breaking Changes**: Clearly document in PR description

## Code Style

- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type Checker**: MyPy
- **Docstrings**: Google style

Example:
```python
def analyze_complexity(file_path: str, threshold: int = 50) -> ComplexityScore:
    """
    Analyze code complexity for a single file.
    
    Args:
        file_path: Absolute path to the file to analyze.
        threshold: Minimum complexity score to flag (default: 50).
        
    Returns:
        ComplexityScore object with detailed metrics.
        
    Raises:
        FileNotFoundError: If file_path does not exist.
        ValueError: If threshold is negative.
    """
    pass
```

## Testing Guidelines

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Mocking**: Use `pytest-mock` for external dependencies
- **Fixtures**: Reuse test data with fixtures

Example:
```python
def test_analyze_simple_file(mock_llm_provider):
    """Test analysis of a simple Python file."""
    analyzer = RepositoryAnalyzer(llm_provider=mock_llm_provider)
    result = analyzer.analyze("https://github.com/test/repo")
    
    assert result.score > 0
    assert len(result.analyzed_files) > 0
```

## Issue Guidelines

### Bug Reports

Include:
- Python version
- OS
- Full error traceback
- Minimal reproducible example

### Feature Requests

Include:
- Use case description
- Expected behavior
- Example usage

## Questions?

Open a [Discussion](https://github.com/liohunter1/ai-complexity-analyzer/discussions) for questions.

Thank you for contributing! 🎉
