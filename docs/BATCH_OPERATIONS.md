# Batch Operations Guide

Learn how to efficiently create multiple Feishu documents from markdown files.

## Overview

Batch operations allow you to migrate an entire folder of markdown documents to Feishu in a single command. The process:

1. **Scan** local folder for markdown files
2. **Create** new Feishu document for each file
3. **Upload** markdown content and images
4. **Report** success/failure statistics

## Quick Start

### Basic Usage

Create documents from all `.md` files in a folder:

```bash
python scripts/batch_create_docs.py ./docs
```

### With Custom Folder

Create documents in a specific Feishu folder:

```bash
python scripts/batch_create_docs.py ./docs --folder fldcnxxxxx
```

### Custom File Pattern

Create documents only from specific files:

```bash
# All markdown files in subfolders
python scripts/batch_create_docs.py ./docs --pattern "**/*.md"

# Custom extension
python scripts/batch_create_docs.py ./docs --pattern "*.markdown"

# Multiple patterns
python scripts/batch_create_docs.py ./docs --pattern "**/*documentation*.md"
```

## Python API

### Basic Example

```python
from lib.feishu_api_client import batch_create_documents_from_folder

result = batch_create_documents_from_folder(
    folder_path="./docs"
)

print(f"Created {result['successful']}/{result['total_files']} documents")
```

### With Options

```python
result = batch_create_documents_from_folder(
    folder_path="./docs",
    feishu_folder_token="fldcnxxxxx",  # Target folder
    pattern="**/*.md",                  # File pattern
    app_id="cli_xxxxx",                 # Custom app ID
    app_secret="xxxxx"                  # Custom app secret
)
```

### Response Structure

```python
{
    "success": True,
    "total_files": 10,
    "successful": 9,
    "failed": 1,

    "documents": [
        {
            "file": "doc1.md",
            "document_id": "doxcnxxxxx",
            "url": "https://feishu.cn/docx/doxcnxxxxx",
            "blocks": 50,
            "images": 3
        },
        # ... more documents
    ],

    "failures": [
        {
            "file": "doc2.md",
            "error": "API request failed: ..."
        }
    ]
}
```

## Real-World Examples

### 1. Migrate Documentation

```bash
# Migrate all documentation to Feishu
python scripts/batch_create_docs.py ./docs

# Result:
# 📊 Batch Creation Summary
# Total Files:    12
# ✅ Successful:  12
# ❌ Failed:      0
```

### 2. Organize by Folder

```bash
# Create source folder structure in Feishu first
python scripts/create_feishu_doc.py --title "Documentation"  # Get folder token

# Create documents in that folder
python scripts/batch_create_docs.py ./docs --folder fldcnxxxxx

# Result: All docs organized in one place
```

### 3. Selective Migration

```bash
# Only migrate specific documentation
python scripts/batch_create_docs.py ./docs --pattern "**/guide/*.md"

# Only API documentation
python scripts/batch_create_docs.py ./docs --pattern "**/api/*.md"

# Exclude archived files
python scripts/batch_create_docs.py ./docs --pattern "**/[!archive]*/*.md"
```

### 4. Preview Before Creating

```python
from pathlib import Path

# Check what will be created
folder = Path("./docs")
files = list(folder.glob("**/*.md"))

print(f"Will create {len(files)} documents:")
for f in files:
    print(f"  • {f.name}")

# Proceed with batch creation
from lib.feishu_api_client import batch_create_documents_from_folder

result = batch_create_documents_from_folder(str(folder))
```

## Error Handling

### Handling Partial Failures

The batch operation continues even if individual files fail:

```python
result = batch_create_documents_from_folder("./docs")

if result['failed'] > 0:
    print(f"⚠️ {result['failed']} files failed:")
    for failure in result['failures']:
        print(f"  ❌ {failure['file']}: {failure['error']}")

    # Retry failed files
    for failure in result['failures']:
        try:
            create_document_from_markdown(
                f"./docs/{failure['file']}"
            )
        except Exception as e:
            print(f"Retry failed for {failure['file']}: {e}")
```

### Common Issues and Solutions

**Issue: Authentication Error**

```
❌ API Error: Failed to get tenant token: ...
```

Solution:
```bash
# Check credentials
export FEISHU_APP_ID=cli_xxxxx
export FEISHU_APP_SECRET=xxxxx

# Or use .env file
cat > .env << EOF
FEISHU_APP_ID=cli_xxxxx
FEISHU_APP_SECRET=xxxxx
EOF
```

**Issue: Invalid Folder Token**

```
❌ API Error: Failed to create document: ...
```

Solution:
```python
# Get root folder token
client = FeishuApiClient.from_env()
root_token = client.get_root_folder_token()
print(f"Use this token: {root_token}")

# Or don't specify --folder (uses root)
python scripts/batch_create_docs.py ./docs
```

**Issue: File Pattern Matches Nothing**

```
INFO: Found 0 markdown files
```

Solution:
```bash
# Check file structure
find ./docs -name "*.md"

# Try different pattern
python scripts/batch_create_docs.py ./docs --pattern "**/*.md"

# Include debugging
python scripts/batch_create_docs.py ./docs -v
```

## Advanced Usage

### Filtering Files

```python
from pathlib import Path

def get_files_to_migrate(folder_path, min_size_kb=1):
    """Get markdown files larger than min_size."""
    folder = Path(folder_path)
    files = []

    for md_file in folder.glob("**/*.md"):
        # Filter by size
        size_kb = md_file.stat().st_size / 1024
        if size_kb < min_size_kb:
            continue

        # Filter by name
        if "draft" in md_file.name.lower():
            continue

        files.append(md_file)

    return files

# Use filtered files
files = get_files_to_migrate("./docs")
for f in files:
    create_document_from_markdown(str(f))
```

### Organizing by Source Folder

```python
from pathlib import Path
from lib.feishu_api_client import create_document_from_markdown

def create_from_subfolders(root_folder, feishu_root_token):
    """Create separate Feishu folders for each source folder."""
    client = FeishuApiClient.from_env()

    for subfolder in Path(root_folder).iterdir():
        if not subfolder.is_dir():
            continue

        # Create folder in Feishu
        folder_result = client.create_folder(
            name=subfolder.name,
            parent_token=feishu_root_token
        )

        # Create documents in this folder
        for md_file in subfolder.glob("*.md"):
            create_document_from_markdown(
                str(md_file),
                folder_token=folder_result['folder_token']
            )

# Usage
create_from_subfolders("./docs", "fldcnxxxxx")
```

### Batch with Logging

```python
import logging
from lib.feishu_api_client import batch_create_documents_from_folder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_create.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Run batch operation
result = batch_create_documents_from_folder("./docs")

# Log summary
logger.info(f"Batch operation completed")
logger.info(f"Total: {result['total_files']}")
logger.info(f"Successful: {result['successful']}")
logger.info(f"Failed: {result['failed']}")

# Log created documents
for doc in result['documents']:
    logger.info(f"Created {doc['file']} -> {doc['url']}")

# Log failures with details
for failure in result['failures']:
    logger.error(f"Failed {failure['file']}: {failure['error']}")
```

## Performance

### Batch Size

By default, batch operations create blocks in groups of 200 (configurable):

```python
# Current behavior (200 blocks per batch)
result = batch_create_documents_from_folder("./docs")

# Adjust batch size (modify FEISHU_BATCH_SIZE in .env)
# Smaller = faster upload, higher memory
# Larger = slower upload, lower memory
```

### Parallel Processing

For large document collections, you can process files in parallel:

```python
from concurrent.futures import ThreadPoolExecutor
from lib.feishu_api_client import create_document_from_markdown
from pathlib import Path

def batch_create_parallel(folder_path, max_workers=3):
    """Create documents in parallel."""
    files = list(Path(folder_path).glob("**/*.md"))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for md_file in files:
            future = executor.submit(
                create_document_from_markdown,
                str(md_file)
            )
            futures.append(future)

        # Collect results
        results = []
        for future in futures:
            try:
                result = future.result(timeout=300)
                results.append(result)
            except Exception as e:
                print(f"Error: {e}")

        return results

# Usage
results = batch_create_parallel("./docs", max_workers=5)
```

## Troubleshooting

### Verbose Output

```bash
# Enable debug logging
python scripts/batch_create_docs.py ./docs -v

# Output will show:
# DEBUG: Requesting tenant token from ...
# DEBUG: Creating document: doc1.md
# INFO: Successfully created document: doxcnxxxxx
```

### Check File Selection

```bash
# Preview what will be created
python -c "
from pathlib import Path
for f in Path('./docs').glob('**/*.md'):
    print(f.name)
"
```

### Validate Folder Token

```python
from lib.feishu_api_client import FeishuApiClient

client = FeishuApiClient.from_env()

# Get root
root = client.get_root_folder_token()
print(f"Root folder: {root}")

# List contents
items = client.list_folder_contents(root)
for item in items:
    print(f"  {item['name']} ({item['type']})")
```

## See Also

- [API_OPERATIONS.md](API_OPERATIONS.md) - Full API reference
- [DIRECT_API_MODE.md](DIRECT_API_MODE.md) - Direct API mode overview
- [create_feishu_doc.py](../scripts/create_feishu_doc.py) - Single document creation
- [batch_create_docs.py](../scripts/batch_create_docs.py) - Batch creation script
