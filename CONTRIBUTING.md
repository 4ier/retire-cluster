# Contributing to Retire-Cluster

First off, thank you for considering contributing to Retire-Cluster! It's people like you that make Retire-Cluster such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include logs and error messages if any

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Follow the Python style guide (PEP 8)
* Include thoughtfully-worded, well-structured tests
* Document new code
* End all files with a newline

## Development Process

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the existing style
6. Issue that pull request!

## Style Guide

### Python Style Guide

We follow PEP 8 with the following additions:

* Line length limit is 100 characters
* Use type hints where possible
* Document all functions and classes with docstrings
* Use meaningful variable names

### Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Example Commit Message

```
Add device auto-discovery feature

- Implement broadcast-based device discovery
- Add configuration for discovery interval
- Update documentation for new feature

Fixes #123
```

## Testing

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=retire_cluster tests/

# Run linting
flake8 retire_cluster/
```

## Documentation

* Use clear and concise language
* Include code examples where appropriate
* Update the README for new features
* Add docstrings to all new functions and classes

## Questions?

Feel free to open an issue with the tag "question" if you have any questions about contributing.