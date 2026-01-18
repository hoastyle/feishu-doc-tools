# Recursive Search Feature for Document Download

## Overview

The `--doc-name` option in `download_doc.py` now performs recursive search across the entire wiki space, making it easier to find documents without knowing their exact path.

## What Changed

### Before (v0.1.0)
- `--doc-name` only searched the root directory
- If multiple documents had the same name, the first one was used (with a warning)
- No visibility into which document was selected

### After (v0.2.0+)
- `--doc-name` recursively searches the **entire wiki space**
- When multiple matches are found, displays all matches with their full paths
- Interactive selection allows users to choose the correct document
- Clear error messages when no matches are found

## How It Works

### 1. Single Match (Direct Use)

When only one document matches the name, it's used automatically:

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "API Overview" \
  -o api_overview.md
```

**Output:**
```
Looking for wiki space: 产品文档
  Found space ID: 7481234567890
Searching for document: API Overview (recursive search)
  Found at: /API/参考/API Overview
Downloading document: doxcn...
```

### 2. Multiple Matches (Interactive Selection)

When multiple documents have the same name:

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "Getting Started" \
  -o getting_started.md
```

**Output:**
```
Looking for wiki space: 产品文档
  Found space ID: 7481234567890
Searching for document: Getting Started (recursive search)

Found 3 documents named 'Getting Started':

  [1] /Getting Started
      Type: doc, Has children: False
  [2] /API/Getting Started
      Type: doc, Has children: True
  [3] /SDK/Python/Getting Started
      Type: doc, Has children: False

Please select a document:
Enter number (1-3): 2

  Selected: /API/Getting Started
Downloading document: doxcn...
```

### 3. No Matches (Clear Error)

When no document is found:

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "NonExistent Doc"
```

**Output:**
```
Looking for wiki space: 产品文档
  Found space ID: 7481234567890
Searching for document: NonExistent Doc (recursive search)
ERROR: Document not found: NonExistent Doc
Searched entire wiki space '产品文档'
Try using --wiki-path to specify the full path if document exists
```

## Technical Details

### Implementation

The feature is implemented through two key functions:

1. **`find_document_by_name_recursive()`**
   - Recursively traverses the wiki space tree
   - Collects all matching documents with their full paths
   - Returns a list of matches with node information

2. **Enhanced `resolve_document_id()`**
   - Handles single match case (direct use)
   - Handles multiple matches case (interactive selection)
   - Handles no match case (clear error)

### Code Structure

```python
def find_document_by_name_recursive(
    client: FeishuApiClient,
    space_id: str,
    doc_name: str,
    parent_token: str = None,
    current_path: str = "",
) -> list[dict]:
    """
    Recursively search for documents by name.

    Returns:
        List of matching nodes with paths
        Each item: {"node": {...}, "path": "/path/to/doc"}
    """
```

### Performance Considerations

- **API Calls**: The search makes one API call per directory level
- **Large Spaces**: For spaces with deep hierarchies, the search may take time
- **Caching**: Node lists are not cached (considers real-time updates)

**Recommendation**: Use `--wiki-path` when you know the exact path for faster access.

## Use Cases

### Use Case 1: Quick Access to Unique Documents

When you know the document name is unique:

```bash
# Fast and simple
uv run python scripts/download_doc.py \
  --space-name "Engineering Docs" \
  --doc-name "Architecture Overview"
```

### Use Case 2: Exploring Similar Documents

When multiple documents share the same name across different sections:

```bash
# Will show all "README" documents across the space
uv run python scripts/download_doc.py \
  --space-name "Project Wiki" \
  --doc-name "README"
```

### Use Case 3: Uncertain Path

When you're not sure where the document is located:

```bash
# Let the tool find it for you
uv run python scripts/download_doc.py \
  --space-name "Company Knowledge Base" \
  --doc-name "Onboarding Guide"
```

## Comparison with `--wiki-path`

| Feature | `--doc-name` | `--wiki-path` |
|---------|-------------|---------------|
| Search scope | Entire space | Specific path |
| Speed | Slower (recursive) | Faster (direct) |
| Use when | Don't know path | Know exact path |
| Multiple matches | Interactive selection | N/A (exact path) |
| Best for | Exploration | Automation |

## Migration from v0.1.0

If you were using `--doc-name` in v0.1.0:

**Old behavior (root-only search):**
```bash
# Only found documents at root level
uv run python scripts/download_doc.py \
  --space-name "Docs" \
  --doc-name "MyDoc"
```

**New behavior (recursive search):**
```bash
# Now finds documents anywhere in the space
uv run python scripts/download_doc.py \
  --space-name "Docs" \
  --doc-name "MyDoc"

# If you get multiple matches when you didn't before,
# use --wiki-path for exact specification:
uv run python scripts/download_doc.py \
  --space-name "Docs" \
  --wiki-path "/MyDoc"  # Specify root explicitly
```

## Testing

A test script is provided to verify the functionality:

```bash
# Run the test
python test_recursive_search.py
```

The test will:
1. Initialize the Feishu API client
2. Find a test wiki space
3. Perform a recursive search
4. Display results with paths

## Error Handling

The feature handles several edge cases:

1. **Empty space**: Clear message if no nodes exist
2. **Cancelled selection**: Gracefully exits on Ctrl+C
3. **Invalid input**: Prompts user to enter valid number
4. **API failures**: Propagates errors with context

## Future Enhancements

Potential improvements for future versions:

1. **Fuzzy matching**: Support partial name matches
2. **Result caching**: Cache search results for repeated queries
3. **Filter by type**: Option to search only documents (exclude folders)
4. **Non-interactive mode**: `--select-first` flag to auto-select first match
5. **Search by pattern**: Regex or wildcard support

## References

- Main implementation: `/scripts/download_doc.py`
- Test script: `/test_recursive_search.py`
- API client: `/lib/feishu_api_client.py`
- Related: Phase 1 download feature (v0.1.0)

---

**Version**: 0.2.0
**Last Updated**: 2026-01-18
**Author**: Enhanced download UX feature
