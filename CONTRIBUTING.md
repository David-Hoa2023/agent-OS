# Contributing to Codex Prime Agent OS

Thank you for your interest in contributing to Codex Prime! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of autonomous agents and LLMs
- Familiarity with async Python (for advanced contributions)

### Finding an Issue

1. Browse the [issue tracker](https://github.com/yourusername/agent-OS/issues)
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on the issue to let others know you're working on it
4. Fork the repository and create a branch

### Areas for Contribution

- **Bug Fixes**: Fix reported bugs or issues
- **Features**: Implement new features from the roadmap
- **Plugins**: Create new plugin examples
- **Documentation**: Improve guides and tutorials
- **Tests**: Add test coverage
- **Performance**: Optimize existing code
- **Examples**: Create usage examples

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/agent-OS.git
cd agent-OS

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/agent-OS.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### 3. Create a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 4. Make Your Changes

Write your code, following the [coding standards](#coding-standards) below.

### 5. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest --cov=codex_prime --cov-report=html

# Run specific test file
pytest tests/test_your_feature.py -v

# Run linting
ruff check codex_prime/ tests/
black --check codex_prime/ tests/
mypy codex_prime/
```

## How to Contribute

### Reporting Bugs

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md):

1. Check if the bug has already been reported
2. Include detailed steps to reproduce
3. Provide system information (OS, Python version, etc.)
4. Include error messages and stack traces
5. Describe expected vs actual behavior

### Suggesting Features

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md):

1. Check if the feature has been suggested
2. Clearly describe the use case
3. Explain why this would be valuable
4. Provide examples or mockups if applicable

### Submitting Changes

1. Create a branch for your changes
2. Make your changes with clear commit messages
3. Add tests for new functionality
4. Update documentation as needed
5. Submit a pull request

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length**: 100 characters (not 79)
- **Imports**: Use absolute imports, grouped by stdlib, third-party, local
- **Type Hints**: Required for all public functions
- **Docstrings**: Google style for all modules, classes, and functions

### Code Quality Tools

```bash
# Format code
black codex_prime/ tests/

# Sort imports
isort codex_prime/ tests/

# Lint code
ruff check codex_prime/ tests/ --fix

# Type checking
mypy codex_prime/ --strict
```

### Example Function

```python
from typing import Optional, List, Dict, Any
from pathlib import Path


def process_memories(
    vault_path: Path,
    query: str,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Process and retrieve memories from the vault.

    Args:
        vault_path: Path to the memory vault directory
        query: Search query string
        limit: Maximum number of results to return
        filters: Optional filters to apply to search

    Returns:
        List of memory dictionaries with scores and metadata

    Raises:
        ValueError: If vault_path doesn't exist
        RuntimeError: If vault is corrupted

    Example:
        >>> results = process_memories(
        ...     vault_path=Path("~/.codex_prime/vault"),
        ...     query="What is Python?",
        ...     limit=5
        ... )
        >>> print(results[0]['text'])
    """
    if not vault_path.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")

    # Implementation...
    results = []
    return results
```

### Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(memory): add vector similarity search

Implement semantic search using ChromaDB for efficient
similarity-based memory retrieval.

- Add VectorStore class
- Integrate with MemoryVault
- Add tests for vector operations

Closes #123
```

```
fix(api): handle timeout errors in provider calls

Add retry logic with exponential backoff for provider API calls
to handle transient network errors.

Fixes #456
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for component interaction
├── e2e/              # End-to-end tests
└── fixtures/         # Test fixtures and data
```

### Writing Tests

```python
import pytest
from pathlib import Path
from codex_prime.memory import MemoryVault


class TestMemoryVault:
    """Test suite for MemoryVault."""

    @pytest.fixture
    def vault(self, tmp_path: Path) -> MemoryVault:
        """Create a temporary vault for testing."""
        return MemoryVault(tmp_path)

    def test_add_ember(self, vault: MemoryVault):
        """Test adding an ember to the vault."""
        # Arrange
        text = "Test memory"
        tags = ["test"]

        # Act
        vault.add_ember(text, tags=tags)

        # Assert
        results = vault.recall("Test", tier="ember")
        assert len(results) > 0
        assert results[0]['text'] == text

    @pytest.mark.asyncio
    async def test_async_operation(self, vault: MemoryVault):
        """Test asynchronous vault operations."""
        result = await vault.async_recall("query")
        assert result is not None
```

### Test Coverage Requirements

- **Minimum**: 70% overall coverage
- **New Features**: 80% coverage required
- **Critical Paths**: 90%+ coverage (security, data handling)

Run coverage:
```bash
pytest --cov=codex_prime --cov-report=term-missing
```

### Async Testing

Use `pytest-asyncio` for async tests:

```python
import pytest


@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await some_async_function()
    assert result is not None
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function(arg1: str, arg2: int = 0) -> bool:
    """Short description of function.

    Longer description if needed. Explain the purpose,
    behavior, and any important notes.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2. Defaults to 0.

    Returns:
        Description of return value

    Raises:
        ValueError: When arg1 is empty
        RuntimeError: When operation fails

    Example:
        >>> result = function("test", 5)
        >>> print(result)
        True
    """
    pass
```

### Updating Documentation

When adding features:

1. Update relevant `.md` files in `/docs`
2. Add examples to `/examples`
3. Update `README.md` if adding major features
4. Update `IMPLEMENTATION_STATUS.md`

### Building Documentation Locally

```bash
# Install documentation dependencies
pip install sphinx sphinx-rtd-theme

# Build documentation
cd docs
make html

# View documentation
open _build/html/index.html
```

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Checklist

1. **Title**: Use clear, descriptive title
2. **Description**: Explain what and why
3. **Testing**: Describe how you tested
4. **Screenshots**: Include if UI changes
5. **Breaking Changes**: Clearly mark and explain
6. **Issue Reference**: Link related issues

### PR Template

```markdown
## Description
Brief description of changes

## Motivation and Context
Why is this change needed? What problem does it solve?

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)

## Additional Notes
```

### Review Process

1. Automated checks run (tests, linting)
2. At least one maintainer review required
3. Address review comments
4. Maintainer merges when approved

### After Merge

- Your branch will be deleted
- Changes will be in the next release
- You'll be added to contributors list

## Plugin Development

### Creating a Plugin

See [Plugin Development Tutorial](docs/PLUGIN_DEVELOPMENT.md) for details.

Quick start:

```bash
# Use the plugin template
cp -r plugins/example-weather-tool plugins/my-plugin
cd plugins/my-plugin

# Edit plugin.yaml and implement your plugin
# Submit PR with your plugin to the community directory
```

### Plugin Guidelines

- Follow the plugin manifest schema
- Include comprehensive README
- Add tests for your plugin
- Security scan must pass
- Document all configuration options

## Community

### Communication Channels

- **GitHub Discussions**: General questions and discussions
- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions

### Getting Help

- Read the [documentation](docs/)
- Check [existing issues](https://github.com/yourusername/agent-OS/issues)
- Ask in [GitHub Discussions](https://github.com/yourusername/agent-OS/discussions)

### Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Project README

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to ask questions in:
- GitHub Discussions for general questions
- Issue comments for specific issues
- Pull request comments for code-specific questions

---

**Thank you for contributing to Codex Prime! 🚀**
