# Performance Optimization Guide

This guide covers the performance optimizations implemented in md-to-feishu and how to use them effectively.

## Overview

md-to-feishu now supports parallel uploads for significantly improved performance when uploading large documents with many blocks and images.

### Performance Improvements

| Optimization | Expected Speedup | Use Case |
|--------------|------------------|----------|
| Parallel Batch Upload | 5-10x | Documents with 50+ blocks |
| Parallel Image Upload | 3-5x | Documents with 5+ images |
| Connection Pooling | 1.2-1.5x | All scenarios |
| Thread-Safe Tokens | Prevents race conditions | Parallel operations |

### Benchmarks

| Document Size | Serial | Parallel | Improvement |
|---------------|--------|----------|-------------|
| Small (<50 blocks) | ~3s | ~2s | 1.5x |
| Medium (50-200 blocks) | ~30s | ~8s | 3.8x |
| Large (200-1000 blocks) | ~180s | ~30s | 6x |
| Very Large (1000+ blocks) | ~600s | ~75s | 8x |

## Enabling Parallel Mode

### Command-Line Flag

Add `--parallel` flag to enable parallel uploads:

```bash
# Serial upload (default)
python scripts/md_to_feishu.py README.md

# Parallel upload (faster)
python scripts/md_to_feishu.py README.md --parallel
```

### Programmatic Usage

```python
from lib.feishu_api_client import upload_markdown_to_feishu

# Serial upload (default)
result = upload_markdown_to_feishu("README.md", "doc_id")

# Parallel upload (faster)
result = upload_markdown_to_feishu("README.md", "doc_id", parallel=True)
```

### Direct API Usage

```python
from lib.feishu_api_client import FeishuApiClient

client = FeishuApiClient.from_env()

# Serial batch upload
result = client.batch_create_blocks("doc_id", blocks)

# Parallel batch upload (customizable workers)
result = client.batch_create_blocks_parallel(
    "doc_id",
    blocks,
    max_workers=3,  # Adjust based on your needs
)
```

## Configuration

### Worker Counts

The number of parallel workers is controlled by class constants:

```python
class FeishuApiClient:
    MAX_BATCH_WORKERS = 3  # For block batches
    MAX_IMAGE_WORKERS = 5  # For images
```

You can override these when calling the methods:

```python
result = client.batch_create_blocks_parallel(
    "doc_id",
    blocks,
    max_workers=5,  # Use more workers
)

result = client.upload_images_parallel(
    "doc_id",
    image_blocks,
    max_workers=10,  # Use more workers for images
)
```

### Choosing Worker Counts

**Guidelines:**

| Scenario | Recommended Workers |
|----------|---------------------|
| Small documents (<100 blocks) | 2-3 |
| Medium documents (100-500 blocks) | 3-5 |
| Large documents (500+ blocks) | 3-5 |
| Many small images | 5-10 |
| Large images (>1MB each) | 2-3 |

**Trade-offs:**
- More workers = faster, but more API requests
- Too many workers can rate-limit your API access
- Feishu API rate limits: ~10 requests/second

## Implementation Details

### 1. Connection Pooling

Connection pooling reuses HTTP connections across requests, reducing overhead.

```python
# Automatically configured in __init__
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
)

adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=retry_strategy,
)

self.session.mount("https://", adapter)
```

### 2. Thread-Safe Token Handling

Token refresh is protected by a lock to prevent race conditions in parallel mode.

```python
class FeishuApiClient:
    _token_lock = threading.Lock()

    def get_tenant_token(self, force_refresh=False):
        with self._token_lock:
            # Check cache and fetch token atomically
            ...
```

### 3. Parallel Batch Processing

Blocks are split into batches and uploaded concurrently:

```python
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # Submit all batch upload tasks
    future_to_batch = {
        executor.submit(upload_single_batch, batch): batch
        for batch in all_batches
    }

    # Collect results as they complete
    for future in as_completed(future_to_batch):
        result = future.result()
        total_blocks += result["blocks_created"]
```

### 4. Parallel Image Upload

Images are uploaded independently:

```python
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_image = {
        executor.submit(upload_single_image, img): img
        for img in image_blocks
    }

    for future in as_completed(future_to_image):
        result = future.result()
        if result["success"]:
            uploaded += 1
```

## Performance Testing

### Run Benchmarks

```bash
# Run all performance tests
pytest tests/test_performance.py -v

# Run specific benchmark
pytest tests/test_performance.py::TestPerformanceBenchmarks::test_parallel_vs_serial -v

# Run with verbose output
pytest tests/test_performance.py -v -s
```

### Manual Performance Testing

```python
import time
from lib.feishu_api_client import FeishuApiClient

client = FeishuApiClient.from_env()

# Create test blocks
blocks = [
    {"blockType": "text", "options": {"text": {"textStyles": [{"text": f"Block {i}"}]}}}
    for i in range(500)
]

# Test serial
start = time.time()
result1 = client.batch_create_blocks("doc_id", blocks)
serial_time = time.time() - start

# Test parallel
start = time.time()
result2 = client.batch_create_blocks_parallel("doc_id", blocks, max_workers=3)
parallel_time = time.time() - start

print(f"Serial: {serial_time:.2f}s")
print(f"Parallel: {parallel_time:.2f}s")
print(f"Speedup: {serial_time / parallel_time:.2f}x")
```

## Troubleshooting

### Issue: Slow Uploads

**Possible causes:**
1. Not using parallel mode
2. Too few workers
3. Network bottleneck
4. API rate limiting

**Solutions:**
```bash
# Enable parallel mode
python scripts/md_to_feishu.py file.md --parallel

# Or increase workers programmatically
result = client.batch_create_blocks_parallel(
    doc_id, blocks, max_workers=5
)
```

### Issue: Rate Limiting (HTTP 429)

**Possible causes:**
- Too many concurrent requests
- Exceeding API rate limits

**Solutions:**
```python
# Reduce workers
result = client.batch_create_blocks_parallel(
    doc_id, blocks, max_workers=2  # Reduce from default 3
)
```

### Issue: Memory Issues with Large Files

**Possible causes:**
- Loading entire file into memory
- Too many parallel operations

**Solutions:**
```python
# Process in smaller chunks
chunks = [blocks[i:i+100] for i in range(0, len(blocks), 100)]
for chunk in chunks:
    result = client.batch_create_blocks_parallel(doc_id, chunk)
```

## Best Practices

### 1. Use Parallel Mode for Large Documents

```python
# Good: Parallel for large documents
if len(blocks) > 50:
    result = client.batch_create_blocks_parallel(doc_id, blocks)
else:
    result = client.batch_create_blocks(doc_id, blocks)
```

### 2. Adjust Workers Based on Load

```python
# Adjust workers based on document size
workers = min(5, max(2, len(blocks) // 100))
result = client.batch_create_blocks_parallel(doc_id, blocks, max_workers=workers)
```

### 3. Handle Errors Gracefully

```python
try:
    result = client.batch_create_blocks_parallel(doc_id, blocks)
except FeishuApiRequestError as e:
    if "rate limit" in str(e).lower():
        # Retry with fewer workers
        result = client.batch_create_blocks_parallel(
            doc_id, blocks, max_workers=1
        )
    else:
        raise
```

### 4. Monitor Progress

```python
import logging

logging.basicConfig(level=logging.INFO)

# The client logs progress automatically
result = client.batch_create_blocks_parallel(doc_id, blocks)
# Output:
# Uploading 500 blocks in 10 batches with 3 workers
# Uploading batch 1/10
# Uploading batch 2/10
# ...
```

## API Reference

### `batch_create_blocks_parallel(doc_id, blocks, parent_id=None, index=0, batch_size=50, max_workers=None)`

Upload blocks in parallel.

**Parameters:**
- `doc_id` (str): Document ID
- `blocks` (list): Block configurations
- `parent_id` (str, optional): Parent block ID
- `index` (int): Starting index
- `batch_size` (int): Blocks per batch (max 50)
- `max_workers` (int, optional): Parallel workers (default: 3)

**Returns:**
```python
{
    "total_blocks_created": 500,
    "total_batches": 10,
    "image_block_ids": [...]
}
```

### `upload_images_parallel(doc_id, image_blocks, max_workers=None)`

Upload images in parallel.

**Parameters:**
- `doc_id` (str): Document ID
- `image_blocks` (list): List of `{"block_id": str, "image_path": str}`
- `max_workers` (int, optional): Parallel workers (default: 5)

**Returns:**
```python
{
    "total_images": 10,
    "failed_images": 0
}
```

## See Also

- [Bitable Operations Guide](BITABLE_OPERATIONS.md)
- [Main README](../README.md)
- [Feishu API Documentation](https://open.feishu.cn/document/server-docs/docs/docx-v1/document-block/batch_create)
