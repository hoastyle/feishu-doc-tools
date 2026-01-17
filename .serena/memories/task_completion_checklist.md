# Task Completion Checklist

When completing a task in this project, follow this checklist to ensure quality:

## 1. Code Quality

### Formatting
- [ ] Run Black formatter on modified files:
  ```bash
  uv run black scripts/ lib/ tests/
  ```

### Linting
- [ ] Run Flake8 to check code style:
  ```bash
  uv run flake8 scripts/ lib/ tests/
  ```
- [ ] Resolve all linting errors and warnings

### Type Checking
- [ ] Run Mypy for type checking:
  ```bash
  uv run mypy scripts/ lib/
  ```
- [ ] Fix any type errors (if applicable)

## 2. Testing

### Run Tests
- [ ] Run all tests to ensure nothing broke:
  ```bash
  uv run pytest tests/
  ```
- [ ] All tests should pass (11 expected to pass)

### Coverage
- [ ] Check test coverage:
  ```bash
  uv run pytest --cov=scripts --cov=lib --cov-report=term-missing tests/
  ```
- [ ] Maintain coverage > 80%
- [ ] Add tests for new functionality

### Manual Testing
- [ ] If applicable, test manually with sample files:
  ```bash
  uv run python scripts/md_to_feishu.py examples/sample.md test_doc --output /tmp/test.json
  ```

## 3. Documentation

### Code Documentation
- [ ] Add/update docstrings for new functions and classes
- [ ] Add inline comments for complex logic
- [ ] Ensure variable names are self-explanatory

### Project Documentation
- [ ] Update README.md if public API changed
- [ ] Update USAGE.md if usage patterns changed
- [ ] Update DESIGN.md if architecture changed

## 4. Git Workflow

### Commit Changes
- [ ] Stage relevant changes:
  ```bash
  git add <files>
  ```
- [ ] Commit with meaningful message:
  ```bash
  git commit -m "<type>: <description>"
  ```
  - Use conventional commit format (feat, fix, docs, etc.)

### Code Review (if applicable)
- [ ] Review your own changes:
  ```bash
  git diff HEAD~1
  ```
- [ ] Ensure no debug code or commented-out code
- [ ] Verify no sensitive information is committed

## 5. Final Checks

### Dependencies
- [ ] If added new dependencies, ensure they're in pyproject.toml
- [ ] Run `uv sync` to update lock file

### Git Status
- [ ] Check git status is clean:
  ```bash
  git status
  ```
- [ ] No unintended files are staged

### Integration Check
- [ ] If changed core modules, test integration with AI workflow
- [ ] Verify JSON output format is compatible with MCP tools

## Quick Command Summary

Run all quality checks at once:
```bash
uv run black scripts/ lib/ tests/ && \
uv run flake8 scripts/ lib/ tests/ && \
uv run mypy scripts/ lib/ && \
uv run pytest --cov=scripts --cov=lib tests/
```

If all pass, commit:
```bash
git add . && \
git commit -m "<type>: <description>" && \
git status
```