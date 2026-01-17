# Code Style and Conventions

## General Principles
- Write clean, readable, and maintainable code
- Follow Python best practices (PEP 8)
- Use meaningful variable and function names
- Add docstrings for classes and public methods
- Keep functions focused and single-purpose

## Formatting

### Black Configuration
- **Line length**: 100 characters
- **Target version**: Python 3.8
- Configuration in `pyproject.toml`:
  ```toml
  [tool.black]
  line-length = 100
  target-version = ['py38']
  ```

### Code Formatter
Use Black for automatic code formatting:
```bash
uv run black scripts/ lib/ tests/
```

## Linting

### Flake8
- Used for style checking
- Should pass without errors before committing

### Mypy
- Used for type checking
- Configuration in `pyproject.toml`:
  ```toml
  [tool.mypy]
  python_version = "3.8"
  warn_return_any = true
  warn_unused_configs = true
  disallow_untyped_defs = false
  ```

## Naming Conventions

### Variables and Functions
- Use `snake_case` for variables and functions
- Examples: `md_file`, `convert_markdown`, `process_tokens`

### Classes
- Use `PascalCase` for class names
- Examples: `MarkdownToFeishuConverter`, `FeishuMdUploader`

### Constants
- Use `UPPER_CASE` for constants
- Example: `LANGUAGE_MAP`, `DEFAULT_BATCH_SIZE`

### Private Methods
- Prefix with underscore `_` for internal methods
- Examples: `_process_heading`, `_extract_inline_text`

## Project-Specific Conventions

### Module Organization
```python
# 1. Standard library imports
import json
import logging
from pathlib import Path

# 2. Third-party imports
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin

# 3. Local imports
from lib.feishu_md_uploader import FeishuMdUploader
```

### Logging
- Use Python's `logging` module
- Configure logger at module level:
  ```python
  logger = logging.getLogger(__name__)
  ```
- Log levels:
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: General informational messages
  - `WARNING`: Warning messages (e.g., skipped images)
  - `ERROR`: Error messages

### Error Handling
- Use try-except blocks for error handling
- Raise meaningful exceptions with clear messages
- Log errors appropriately

### Documentation

#### Docstrings
Use Google-style docstrings:
```python
def function_name(param1: str, param2: int) -> dict:
    """Brief description of function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When invalid input is provided
    """
```

#### Comments
- Use comments to explain "why", not "what"
- Keep comments concise and up-to-date
- Avoid obvious comments

### Type Hints
- Use type hints for function parameters and return values
- Example:
  ```python
  def convert(self, md_file: Path, doc_id: str) -> dict:
      ...
  ```

## Testing Conventions

### Test File Organization
- Test files should be named `test_*.py`
- Test functions should be named `test_*`
- Use pytest fixtures for setup

### Test Structure
```python
def test_feature_name():
    # Arrange: Set up test data
    input_data = ...
    
    # Act: Execute the code being tested
    result = function_under_test(input_data)
    
    # Assert: Verify the results
    assert result == expected
```

### Coverage Target
- Maintain test coverage > 80%
- Run tests with coverage report:
  ```bash
  uv run pytest --cov=scripts --cov=lib --cov-report=term-missing tests/
  ```

## Git Commit Conventions

### Commit Message Format
```
<type>: <subject>

<body> (optional)
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Build process or auxiliary tool changes

### Examples
```
feat: add support for tables in markdown conversion
fix: handle empty markdown files correctly
docs: update usage guide with new options
test: add tests for image handling
```