# Feishu API Operations - Reference Guide

This document provides comprehensive reference for all Feishu API operations available in md-to-feishu.

## Overview

md-to-feishu now supports both **upload** and **create** operations:

| Operation | Purpose | API Endpoint | Best For |
|-----------|---------|--------------|----------|
| **Upload** | Add content to existing document | `/docx/v1/documents/{doc_id}/blocks` | Updating existing docs |
| **Create** | Create new document from markdown | `/docx/v1/documents` | Batch migrations, new docs |
| **Folder** | Manage folder structure | `/drive/v1/folders` | Organization |
| **Image** | Upload and bind images | `/docx/v1/media/upload` | Rich content |

## Document Operations

### Create Document

Create a new Feishu document.

**Python API:**

```python
from lib.feishu_api_client import FeishuApiClient

client = FeishuApiClient.from_env()

# Create in root folder
result = client.create_document(
    title="My Document"
)

# Create in specific folder
result = client.create_document(
    title="My Document",
    folder_token="fldcnxxxxx"
)

print(result["document_id"])
print(result["url"])
```

**Response:**

```python
{
    "document_id": "doxcnxxxxx",
    "url": "https://feishu.cn/docx/doxcnxxxxx",
    "title": "My Document",
    "revision_id": 1
}
```

**API Details:**

- **Endpoint**: `POST /docx/v1/documents`
- **Authentication**: Bearer {tenant_access_token}
- **Rate Limit**: 100 requests/minute
- **Timeout**: 10 seconds

### Upload Content to Document

Upload markdown content to a document.

**Python API:**

```python
from lib.feishu_api_client import upload_markdown_to_feishu

# Upload to existing document
result = upload_markdown_to_feishu(
    md_file="README.md",
    doc_id="doxcnxxxxx"
)

print(f"Created {result['total_blocks']} blocks")
print(f"Uploaded {result['total_images']} images")
```

**Response:**

```python
{
    "success": True,
    "document_id": "doxcnxxxxx",
    "document_url": "https://feishu.cn/docx/doxcnxxxxx",
    "total_blocks": 50,
    "total_images": 3,
    "total_batches": 1
}
```

**API Details:**

- **Batch Size**: 200 blocks per request (configurable)
- **Max File Size**: 20MB per markdown file
- **Image Formats**: PNG, JPG, GIF, WebP
- **Rate Limit**: 100 requests/minute

### Create Document from Markdown

Create a new document and upload markdown content in one operation.

**Python API:**

```python
from lib.feishu_api_client import create_document_from_markdown

result = create_document_from_markdown(
    md_file="README.md",
    title="My Document",
    folder_token="fldcnxxxxx"
)

print(f"Created: {result['document_url']}")
```

**Response:**

```python
{
    "success": True,
    "document_id": "doxcnxxxxx",
    "document_url": "https://feishu.cn/docx/doxcnxxxxx",
    "title": "My Document",
    "total_blocks": 50,
    "total_images": 3,
    "total_batches": 1
}
```

**Workflow:**

1. Create new document with title
2. Convert markdown to blocks
3. Upload blocks (batched)
4. Upload and bind images

## Folder Operations

### Get Root Folder Token

Get the root folder token for your workspace.

**Python API:**

```python
client = FeishuApiClient.from_env()

root_token = client.get_root_folder_token()
print(root_token)
```

**API Details:**

- **Endpoint**: `GET /drive/v1/metas/root_folder_meta`
- **Returns**: Folder token for workspace root
- **Use Case**: Default target for document creation

### Create Folder

Create a new folder in Feishu Drive.

**Python API:**

```python
result = client.create_folder(
    name="My Folder",
    parent_token="fldcnxxxxx"  # Optional, defaults to root
)

print(result["folder_token"])
print(result["url"])
```

**Response:**

```python
{
    "folder_token": "fldcnxxxxx",
    "name": "My Folder",
    "url": "https://feishu.cn/drive/folder/fldcnxxxxx"
}
```

**API Details:**

- **Endpoint**: `POST /drive/v1/folders`
- **Parent**: Defaults to root if not specified
- **Naming**: Max 200 characters

### List Folder Contents

List files and folders in a folder.

**Python API:**

```python
items = client.list_folder_contents(
    folder_token="fldcnxxxxx",
    page_size=200
)

for item in items:
    print(f"{item['name']} ({item['type']})")
```

**Response:**

```python
[
    {
        "name": "document1.docx",
        "type": "file",
        "created_time": 1234567890,
        "modified_time": 1234567890
    },
    {
        "name": "subfolder",
        "type": "folder",
        "folder_token": "fldcnxxxxx"
    }
]
```

**API Details:**

- **Endpoint**: `GET /drive/v1/files?folder_token={token}`
- **Page Size**: Max 200 items
- **Pagination**: Use has_more and page_token

## Batch Operations

### Batch Create Documents

Create multiple documents from a folder of markdown files.

**Python API:**

```python
from lib.feishu_api_client import batch_create_documents_from_folder

result = batch_create_documents_from_folder(
    folder_path="./docs",
    feishu_folder_token="fldcnxxxxx",
    pattern="*.md"
)

print(f"Created {result['successful']}/{result['total_files']} documents")

for failure in result['failures']:
    print(f"Failed: {failure['file']}: {failure['error']}")
```

**Response:**

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
        }
    ],
    "failures": [
        {
            "file": "doc2.md",
            "error": "..."
        }
    ]
}
```

**Features:**

- **Error Recovery**: Continues on individual file failures
- **Progress Logging**: Real-time updates for each file
- **Pattern Matching**: Supports glob patterns (*.md, **/*.md)
- **Folder Structure**: Can use recursive patterns

## Block Operations

### Create Text Block

```python
blocks = [{
    "blockType": "text",
    "options": {
        "text": {
            "textStyles": [{
                "text": "Hello World",
                "style": {
                    "bold": True,
                    "italic": False
                }
            }],
            "align": 1  # 1=left, 2=center, 3=right
        }
    }
}]

result = client.batch_create_blocks(doc_id, blocks)
```

### Create Heading Block

```python
blocks = [{
    "blockType": "heading1",  # heading1-9
    "options": {
        "heading": {
            "level": 1,
            "content": "Section Title",
            "align": 1
        }
    }
}]
```

### Create Code Block

```python
blocks = [{
    "blockType": "code",
    "options": {
        "code": {
            "code": "print('Hello')",
            "language": 49  # Python
        }
    }
}]
```

**Language Codes:**

- 1: PlainText
- 30: JavaScript
- 49: Python
- 52: Ruby
- 56: SQL

### Create List Block

```python
blocks = [{
    "blockType": "list",
    "options": {
        "list": {
            "content": "Item 1",
            "isOrdered": False,  # True for ordered list
            "align": 1
        }
    }
}]
```

### Create Image Block

```python
# Create empty image block
blocks = [{
    "blockType": "image",
    "options": {
        "image": {
            "align": 2  # 1=left, 2=center, 3=right
        }
    }
}]

# Upload and bind image
client.upload_and_bind_image(
    doc_id="doxcnxxxxx",
    block_id="block_id_from_response",
    image_path_or_url="path/to/image.png"
)
```

## Error Handling

### Common Errors

**FeishuApiAuthError**

```python
try:
    client = FeishuApiClient.from_env()
except FeishuApiAuthError as e:
    print(f"Authentication failed: {e}")
    # Check FEISHU_APP_ID and FEISHU_APP_SECRET
```

**FeishuApiRequestError**

```python
try:
    result = client.create_document("Test")
except FeishuApiRequestError as e:
    print(f"API request failed: {e}")
    # Check folder token exists, permissions, etc.
```

### Retry Strategy

```python
import time

def create_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.create_document("Test")
        except FeishuApiRequestError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
```

## Rate Limiting

Feishu API has the following rate limits:

- **Document Creation**: 100 requests/minute
- **Block Creation**: 100 requests/minute
- **Image Upload**: 50 requests/minute
- **Folder Operations**: 100 requests/minute

**Handling Rate Limits:**

```python
import time
from requests.exceptions import HTTPError

def create_with_backoff(client, titles):
    for title in titles:
        try:
            client.create_document(title)
        except HTTPError as e:
            if e.response.status_code == 429:
                # Rate limited, wait before retry
                time.sleep(60)
                client.create_document(title)
            else:
                raise
```

## Best Practices

### 1. Use Environment Variables

```python
import os
from lib.feishu_api_client import FeishuApiClient

# Set in .env file
client = FeishuApiClient.from_env()
```

### 2. Handle Errors Gracefully

```python
from lib.feishu_api_client import FeishuApiClientError

try:
    result = client.create_document("Test")
except FeishuApiClientError as e:
    logger.error(f"Operation failed: {e}")
    # Take appropriate action
```

### 3. Batch Operations for Efficiency

```python
# Instead of creating one at a time
for file in files:
    client.create_document(...)

# Use batch operation
batch_create_documents_from_folder(folder)
```

### 4. Validate Input

```python
from pathlib import Path

md_file = Path("README.md")
if not md_file.exists():
    raise FileNotFoundError(f"File not found: {md_file}")
if not md_file.suffix == ".md":
    raise ValueError(f"Expected .md file, got: {md_file.suffix}")
```

### 5. Log Operations

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Creating document: {title}")
result = client.create_document(title)
logger.info(f"Created: {result['document_id']}")
```

## CLI Reference

### Create Single Document

```bash
# Create in root folder
uv run python scripts/create_feishu_doc.py README.md

# Create with custom title
uv run python scripts/create_feishu_doc.py README.md --title "My Document"

# Create in specific folder
uv run python scripts/create_feishu_doc.py README.md --folder fldcnxxxxx

# Custom credentials
uv run python scripts/create_feishu_doc.py README.md \
  --app-id cli_xxxxx --app-secret xxxxx
```

### Batch Create Documents

```bash
# Create from all .md files
uv run python scripts/batch_create_docs.py ./docs

# Create in specific folder
uv run python scripts/batch_create_docs.py ./docs --folder fldcnxxxxx

# Custom file pattern
uv run python scripts/batch_create_docs.py ./docs --pattern "*.markdown"

# Recursive search
uv run python scripts/batch_create_docs.py ./docs --pattern "**/*.md"
```

## See Also

- [BATCH_OPERATIONS.md](BATCH_OPERATIONS.md) - Detailed batch operations guide
- [DIRECT_API_MODE.md](DIRECT_API_MODE.md) - Direct API mode overview
- [Feishu API Documentation](https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create)
