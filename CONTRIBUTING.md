# Contributing to ForgeAI

We welcome contributions to ForgeAI! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/forgeai.git
   cd forgeai
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Frontend Development

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

When creating a bug report, include:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)

### Suggesting Features

Feature suggestions are welcome. Please provide:
- A clear description of the feature
- Use cases
- Any relevant examples

### Pull Requests

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes
3. Add or update tests as needed
4. Ensure all tests pass:
   ```bash
   pytest
   ```

5. Run linting and type checks:
   ```bash
   ruff check .
   mypy --strict
   ```

6. Commit your changes with a descriptive message
7. Push to your fork and submit a pull request

### Commit Messages

Use clear, descriptive commit messages:
- `feat: add new pruning algorithm`
- `fix: resolve memory leak in benchmark`
- `docs: update API documentation`
- `test: add unit tests for quantization`
- `refactor: simplify optimization pipeline`

### Code Style

- Follow PEP 8 for Python code
- Use type hints for all functions
- Write Google-style docstrings
- Keep functions focused and concise
- Use meaningful variable names

### Testing

- Write tests for new features
- Aim for >90% test coverage
- Use pytest fixtures for common setup
- Mock external dependencies

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for project architecture details.

## Questions?

Feel free to open an issue for any questions about contributing.
