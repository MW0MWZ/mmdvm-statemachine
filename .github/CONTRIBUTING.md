# Contributing to MMDVM State Machine

Thank you for your interest in contributing to the MMDVM State Machine project! This document provides guidelines and information for contributors.

## Code of Conduct

Be respectful, constructive, and professional in all interactions. This is an amateur radio and educational project - we're all here to learn and improve.

## How to Contribute

### Reporting Bugs

Report bugs at: https://github.com/MW0MWZ/mmdvm-statemachine/issues

Before creating a bug report:
1. Check existing issues to avoid duplicates: https://github.com/MW0MWZ/mmdvm-statemachine/issues
2. Verify you're using the latest version
3. Test with the example configuration

When creating a bug report, include:
- Operating system and version (Debian/Alpine/Ubuntu version)
- Python version (`python3 --version`)
- MMDVMHost version and configuration
- Complete error messages and stack traces
- Steps to reproduce the issue
- Configuration file (sanitized of sensitive data)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:
1. Check existing issues and pull requests
2. Clearly describe the use case and benefit
3. Explain how it fits with the project goals
4. Consider if it should be configurable

### Pull Requests

1. Fork the repository: https://github.com/MW0MWZ/mmdvm-statemachine
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the coding standards below
4. Add or update tests as needed
5. Update documentation
6. Commit with clear, descriptive messages
7. Push to your fork
8. Open a pull request

#### Pull Request Guidelines

- One feature or fix per pull request
- Include tests for new functionality
- Update documentation including docstrings
- Follow existing code style
- Add yourself to contributors if you'd like

## Development Setup

### Initial Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/mmdvm-statemachine.git
cd mmdvm-statemachine

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies including development tools
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov black mypy pylint
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mmdvm_statemachine --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v
```

### Code Quality Checks

```bash
# Format code with black
black src/ tests/

# Type checking with mypy
mypy src/

# Linting with pylint
pylint src/
```

## Coding Standards

### Python Style

- Follow PEP 8 style guide
- Use Black for code formatting (line length: 100)
- Use type hints for all functions
- Maximum line length: 100 characters
- Use meaningful variable and function names

### Code Organization

- Keep functions focused and small
- Use Pydantic models for data validation
- Prefer composition over inheritance
- Write docstrings for all public functions and classes

### Docstring Format

Use Google-style docstrings:

```python
def process_qso(data: dict) -> QSO:
    """Process raw QSO data into a QSO model.

    Args:
        data: Dictionary containing raw QSO data from log parser

    Returns:
        Validated QSO model instance

    Raises:
        ValueError: If data is invalid or incomplete
    """
    pass
```

### Testing

- Write tests for all new functionality
- Aim for >80% code coverage
- Test edge cases and error conditions
- Use descriptive test names
- Use pytest fixtures for common setup

Example test:

```python
def test_qso_creation_with_valid_data():
    """Test that QSO model is created correctly with valid data."""
    qso = QSO(
        mode=Mode.DMR,
        source_callsign="N0CALL",
        destination_callsign="N1CALL"
    )
    assert qso.mode == Mode.DMR
    assert qso.source_callsign == "N0CALL"
```

### Commit Messages

Use clear, descriptive commit messages:

```
Add support for P25 log parsing

- Implement P25LogParser class
- Add tests for P25 log format
- Update documentation with P25 examples

Fixes #123
```

Format:
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed description if needed
- Reference issues with "Fixes #123" or "Relates to #456"

## Architecture Guidelines

### Adding New Features

When adding new features:
1. Review existing architecture in `docs/DEVELOPMENT.md`
2. Consider configurability (add to Config model)
3. Add appropriate logging
4. Handle errors gracefully
5. Update API documentation if adding endpoints
6. Consider backwards compatibility

### Performance Considerations

- Use async/await for I/O operations
- Avoid blocking the event loop
- Use appropriate data structures (deque for bounded queues)
- Profile before optimizing
- Document performance characteristics

### Security

- Validate all input data
- Sanitize data before logging
- Never log sensitive information
- Use Pydantic for input validation
- Follow principle of least privilege

## Documentation

### Code Documentation

- Docstrings for all public classes and functions
- Inline comments for complex logic
- Type hints for all functions
- Update README.md for user-facing changes

### User Documentation

Update appropriate documentation:
- `README.md` - Installation and basic usage
- `docs/QUICKSTART.md` - Getting started guide
- `docs/DEVELOPMENT.md` - Architecture and development
- `config.example.yaml` - Configuration options

## Release Process

Maintainers will:
1. Review and test pull requests
2. Update version numbers
3. Update CHANGELOG.md
4. Create release tags
5. Build and publish releases

## Questions?

- Open an issue for questions about contributing
- Check existing documentation in `docs/`
- Review closed issues and pull requests for examples

## License

By contributing, you agree that your contributions will be licensed under the same terms as the project.

Thank you for contributing to MMDVM State Machine!
