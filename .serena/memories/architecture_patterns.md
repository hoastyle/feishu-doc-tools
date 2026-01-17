# Architecture Patterns and Design

## Design Philosophy

### Core Principle: Zero Context Usage
The primary design goal is to enable uploading large Markdown files to Feishu without consuming AI model context tokens.

### Solution: Intermediary Script Pattern
```
Markdown → Python Script → JSON → AI + MCP → Feishu
```

**Benefits**:
- File content doesn't enter AI context
- Supports arbitrary file sizes
- Structured JSON for easy processing
- Independently testable components

## Module Architecture

### 1. Converter Module (`scripts/md_to_feishu.py`)

**Purpose**: Parse Markdown and convert to Feishu block format

**Key Components**:
- `MarkdownToFeishuConverter`: Main converter class
- `LANGUAGE_MAP`: Maps markdown language codes to Feishu codes
- `logger`: Logging configuration

**Key Methods**:
- `convert()`: Main entry point, orchestrates conversion
- `_process_tokens()`: Traverses markdown AST
- `_process_heading()`, `_process_paragraph()`, etc.: Handle specific block types
- `_extract_inline_styles()`: Handles inline formatting (bold, italic, etc.)
- `_create_batches()`: Splits blocks into batches of 50
- `_generate_upload_instructions()`: Creates human-readable instructions

**Design Patterns**:
- **Strategy Pattern**: Different processors for different markdown elements
- **Builder Pattern**: Incrementally builds block structures
- **Batch Processing**: Automatically splits large documents

### 2. Uploader Module (`lib/feishu_md_uploader.py`)

**Purpose**: Wrapper class for AI integration

**Key Components**:
- `FeishuMdUploader`: Main uploader class
- `upload_md_to_feishu()`: Convenience function

**Key Methods**:
- `convert_md_to_json()`: Calls converter script
- `prepare_mcp_calls()`: Extracts MCP call parameters from JSON
- `generate_upload_instructions()`: Creates upload instructions for AI

**Design Patterns**:
- **Facade Pattern**: Simplifies interface for AI agents
- **Command Pattern**: Generates structured commands for MCP tools

### 3. Test Module (`tests/test_md_to_feishu.py`)

**Purpose**: Comprehensive unit testing

**Coverage**:
- Basic conversion functionality
- Heading, code block, list conversions
- Text style handling (bold, italic, code)
- Batch creation logic
- Long paragraph splitting
- Image handling (local and network)
- Error handling
- Edge cases (empty files)

## Data Flow Architecture

### Stage 1: Markdown → AST
```python
MarkdownIt().parse(markdown_text)
# Produces: Token tree
```

### Stage 2: AST → Blocks
```python
_process_tokens(tokens)
# Produces: List[dict] (Feishu block format)
```

### Stage 3: Blocks → Batches
```python
_create_batches(blocks, batch_size=50)
# Produces: List[Batch]
```

### Stage 4: Batches → JSON
```python
{
  "success": bool,
  "documentId": str,
  "batches": [...],
  "images": [...],
  "metadata": {...}
}
```

### Stage 5: JSON → MCP Calls
```python
# AI reads JSON and calls:
batch_create_feishu_blocks(documentId, parentBlockId, index, blocks)
upload_and_bind_image_to_block(documentId, images)
```

## Key Design Decisions

### Batch Size: 50 blocks
- Balances API limits and performance
- Configurable via `--batch-size` parameter
- Prevents timeouts on large documents

### Image Handling Modes
1. **local** (default): Only local images
2. **download**: Download network images (to be implemented)
3. **skip**: Skip all images

### Text Length Limit: 2000 characters
- Prevents oversized text blocks
- Automatically splits long paragraphs
- Configurable via `--max-text-length`

### Language Code Mapping
- Maps 50+ markdown language codes to Feishu codes
- Extensible LANGUAGE_MAP constant
- Defaults to PlainText if language not found

## Error Handling Strategy

### Graceful Degradation
- Skip problematic elements with warnings
- Continue processing remaining content
- Log errors for debugging

### Error Categories
1. **Parse Errors**: Logged but don't stop conversion
2. **File Errors**: Raised immediately (file not found, etc.)
3. **Image Errors**: Logged as warnings, continue without image

### Logging Levels
- `DEBUG`: Detailed token processing
- `INFO`: Conversion progress
- `WARNING`: Skipped elements, degraded functionality
- `ERROR`: Critical failures

## Extension Points

### Adding New Block Types
1. Add processor method: `_process_<type>()`
2. Update `_process_tokens()` switch logic
3. Add corresponding tests

### Adding New Image Modes
1. Add mode to argument parser
2. Implement handler in `_handle_image()`
3. Update documentation

### Supporting New Formats
1. Create new converter class (inherit patterns)
2. Reuse JSON output format
3. Use same uploader interface

## Performance Considerations

### Memory Efficiency
- Stream processing of tokens
- Batch processing prevents memory overflow
- JSON intermediate format is compact

### Time Complexity
- O(n) for token traversal
- O(n) for batch creation
- Total: O(n) where n = number of markdown elements

### Optimization Opportunities
- Parallel batch uploads (future enhancement)
- Caching of language mappings
- Async image downloads

## Security Considerations

### File Access
- Validates file paths
- Relative paths resolved from markdown file location
- No arbitrary file system access

### Image Handling
- Network images require explicit mode
- Local paths validated
- No remote code execution

### Input Validation
- Document ID validated
- Image paths sanitized
- Safe JSON serialization