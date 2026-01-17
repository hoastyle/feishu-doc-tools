# Suggested Commands for md-to-feishu

## Dependency Management

### Install uv (if not installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install dependencies
```bash
# Install project dependencies
uv sync

# Install with dev dependencies
uv sync --extra dev
```

## Basic Usage

### Convert Markdown to JSON
```bash
# Basic conversion
uv run python scripts/md_to_feishu.py <md_file_path> <feishu_doc_id> --output /tmp/blocks.json

# With options
uv run python scripts/md_to_feishu.py examples/sample.md doc_id \
  --output /tmp/output.json \
  --batch-size 50 \
  --image-mode local \
  --max-text-length 2000 \
  --verbose
```

### Use Tool Class (for AI integration)
```bash
uv run python -c "from lib.feishu_md_uploader import FeishuMdUploader; \
           uploader = FeishuMdUploader(); \
           uploader.upload('<md_file>', '<doc_id>')"
```

## Testing

### Run all tests
```bash
uv run pytest tests/
```

### Run specific test file
```bash
uv run pytest tests/test_md_to_feishu.py -v
```

### Run with coverage
```bash
uv run pytest --cov=scripts --cov=lib tests/
```

### Run with coverage report
```bash
uv run pytest --cov=scripts --cov=lib --cov-report=term-missing tests/
```

## Code Quality

### Format code with black
```bash
uv run black scripts/ lib/ tests/
```

### Check code style with flake8
```bash
uv run flake8 scripts/ lib/ tests/
```

### Type check with mypy
```bash
uv run mypy scripts/ lib/
```

### Run all quality checks
```bash
uv run black scripts/ lib/ tests/ && \
uv run flake8 scripts/ lib/ tests/ && \
uv run mypy scripts/ lib/ && \
uv run pytest --cov=scripts --cov=lib tests/
```

## Git Commands

### Standard git workflow
```bash
# Check status
git status

# Add changes
git add .

# Commit with message
git commit -m "feat: add new feature"

# Push to remote
git push origin master
```

## System Utilities (Linux)

### List files
```bash
ls -la
```

### Search files
```bash
find . -name "*.py" -type f
```

### Search in files
```bash
grep -r "pattern" scripts/ lib/
```

### View file content
```bash
cat file.py
head -n 20 file.py
tail -n 20 file.py
```

### Navigate directories
```bash
cd /path/to/directory
pwd
```

## Project Specific

### View conversion result
```bash
cat /tmp/output.json | jq '.metadata'
```

### Check supported languages
```bash
uv run python -c "from scripts.md_to_feishu import LANGUAGE_MAP; print(LANGUAGE_MAP)"
```

### Quick test run
```bash
uv run python scripts/md_to_feishu.py examples/sample.md test_doc_id --output /tmp/test.json && cat /tmp/test.json | jq
```