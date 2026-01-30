# Django Trademark Agent Development Guide

## Commands
- `just ask "Your question here"` - Run the trademark agent with a question
- `just demo` - Run a demo with a sample question
- `just lint` - Run pre-commit checks on all files
- `just lint path/to/file.py` - Run pre-commit on specific file(s)
- `just fmt` - Format code using just's built-in formatter
- `just bootstrap` - Install pip and uv package management tools
- `ruff check .` - Lint Python files with ruff
- `ruff format .` - Format Python files with ruff

## Code Style
- Python version: >=3.12
- Line length: 120 characters
- Imports: standard library first, then third-party, then local (sorted alphabetically)
- Use type annotations throughout
- Class naming: PascalCase (e.g., `Result`)
- Function naming: snake_case (e.g., `fetch_and_cache`)
- Parameter naming: snake_case with clear descriptive names
- Error handling: Use explicit error handling with appropriate status checks
- Docstrings: Not enforced but recommended for complex functions
- Use f-strings for string formatting
- Linting: Ruff with select=["E", "F"], ignoring E501 (line length) and E741
