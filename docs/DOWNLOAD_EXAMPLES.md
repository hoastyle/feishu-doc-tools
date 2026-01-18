# Download Document - Quick Examples

## Method 3: Search by Document Name (Recursive)

The `--doc-name` option searches the entire wiki space recursively.

### Example 1: Single Match

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "API Overview" \
  -o api_overview.md
```

**When to use**: You know the document name is unique in the space.

### Example 2: Multiple Matches with Interactive Selection

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "README"
```

**Output:**
```
Found 3 documents named 'README':

  [1] /README
      Type: doc, Has children: False
  [2] /API/README
      Type: doc, Has children: True
  [3] /SDK/Python/README
      Type: doc, Has children: False

Please select a document:
Enter number (1-3): 2
```

**When to use**: Multiple documents share the same name; you want to see all options.

### Example 3: No Output Path (Auto-generate)

```bash
uv run python scripts/download_doc.py \
  --space-name "Engineering" \
  --doc-name "Architecture Diagram"
```

Will save to: `Architecture_Diagram.md`

### Example 4: With Verbose Logging

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "Getting Started" \
  -v \
  -o getting_started.md
```

Shows detailed search progress.

## When to Use `--doc-name` vs `--wiki-path`

### Use `--doc-name` when:
- You don't know the exact path
- You want to explore available documents
- The document name is likely unique
- You're okay with interactive selection

### Use `--wiki-path` when:
- You know the exact path
- You're automating (scripts)
- You want faster execution
- You need deterministic behavior

## Common Scenarios

### Scenario 1: Finding a specific guide

```bash
uv run python scripts/download_doc.py \
  --space-name "Company Wiki" \
  --doc-name "Onboarding Guide"
```

### Scenario 2: Downloading API documentation

```bash
uv run python scripts/download_doc.py \
  --space-name "Developer Portal" \
  --doc-name "REST API Reference" \
  -o rest_api.md
```

### Scenario 3: Exploring documentation structure

```bash
# First, search to see where the document is
uv run python scripts/download_doc.py \
  --space-name "Project Docs" \
  --doc-name "Installation"

# Then use exact path for future downloads
uv run python scripts/download_doc.py \
  --space-name "Project Docs" \
  --wiki-path "/Setup/Installation"
```

## Tips

1. **Start with `--doc-name`** to explore and find the document
2. **Switch to `--wiki-path`** once you know the exact location
3. **Use `-v` flag** to see search progress for large spaces
4. **Omit `-o`** to auto-generate filename from document title
5. **Press Ctrl+C** to cancel interactive selection

## Troubleshooting

### "Document not found"

```
ERROR: Document not found: MyDoc
Searched entire wiki space 'MySpace'
```

**Solutions:**
- Check spelling of document name (case-sensitive)
- Verify you're searching in the correct space
- Use wiki web interface to confirm document exists
- Try `--wiki-path` if you know the path

### "Multiple documents found but want automation"

Use `--wiki-path` for deterministic selection:

```bash
# Instead of interactive selection
uv run python scripts/download_doc.py \
  --space-name "Docs" \
  --wiki-path "/API/REST API"  # Exact path
```

### Slow search in large spaces

For very large wiki spaces:

```bash
# Use --wiki-path for faster direct access
uv run python scripts/download_doc.py \
  --space-name "Large Wiki" \
  --wiki-path "/Section/Subsection/Document"
```

---

**See also:**
- [RECURSIVE_SEARCH_FEATURE.md](./RECURSIVE_SEARCH_FEATURE.md) - Detailed feature documentation
- [DOWNLOAD_FUNCTION_REVIEW.md](./DOWNLOAD_FUNCTION_REVIEW.md) - Complete feature review
