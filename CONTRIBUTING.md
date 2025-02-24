# Contributing to Booth Assets Manager

First off, thank you for considering contributing to Booth Assets Manager! It's people like you that make it a great tool for everyone.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if relevant
* Include your Python version and operating system

### Suggesting Enhancements

If you have a suggestion for the project, we'd love to hear it! Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* A clear and descriptive title
* A detailed description of the proposed feature
* Any possible drawbacks or considerations
* If possible, a rough implementation approach

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Follow the Python coding style (PEP 8)
* Include appropriate tests if adding new functionality
* Update documentation for any changed functionality
* Ensure all tests pass

## Development Process

1. Fork the repo and create your branch from `main`
2. Install development dependencies: `pip install -e ".[dev]"`
3. Make your changes
4. Run the tests and ensure they all pass
5. Update documentation if needed
6. Create your pull request

### Local Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/booth-assets-manager.git
cd booth-assets-manager

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Running Tests

```bash
python -m pytest tests/
```

## Style Guidelines

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Python Style Guide

This project follows PEP 8 with some specific rules:

* Use 4 spaces for indentation
* Use docstrings for all public modules, functions, classes, and methods
* Keep line length to 88 characters (using Black formatter)
* Use type hints where appropriate

## Additional Notes

### Issue and Pull Request Labels

* `bug`: Something isn't working
* `enhancement`: New feature or request
* `documentation`: Improvements or additions to documentation
* `good first issue`: Good for newcomers
* `help wanted`: Extra attention is needed

## Questions?

Feel free to open an issue with your question or reach out to the maintainers directly.

Thank you for contributing to Booth Assets Manager!
