# Project Overview: md-to-feishu

## Purpose
A tool to upload Markdown files to Feishu documents without consuming AI model context. The project converts Markdown files to JSON format, which is then uploaded to Feishu using MCP (Model Context Protocol) tools.

## Key Features
- ✅ Zero context usage - supports arbitrary size Markdown files
- ✅ Format preservation - supports headings, paragraphs, code blocks, lists, tables, images
- ✅ Batch processing - automatic batching (50 blocks/batch)
- ✅ Image support - local images, network images, multiple processing modes
- ✅ Error-friendly - clear error messages and logging

## Architecture
```
Markdown File → Python Script Parse → JSON Format → AI calls MCP tools → Feishu Document
```

**Key Advantages**:
- File content doesn't enter model context
- Uses structured JSON to pass information
- Can be independently tested and extended

## Tech Stack
- **Language**: Python 3.8.1+
- **Package Manager**: uv (modern Python dependency manager)
- **Core Dependencies**:
  - markdown-it-py >= 3.0.0 (Markdown parser)
  - mdit-py-plugins >= 0.4.0 (Markdown plugins)
- **Dev Dependencies**:
  - pytest >= 7.0.0 (testing)
  - pytest-cov >= 4.0.0 (coverage)
  - black >= 23.0.0 (formatter)
  - flake8 >= 6.0.0 (linter)
  - mypy >= 1.0.0 (type checker)

## Project Structure
```
md-to-feishu/
├── scripts/
│   └── md_to_feishu.py       # Core conversion script
├── lib/
│   └── feishu_md_uploader.py # Tool class wrapper
├── tests/
│   └── test_md_to_feishu.py  # Unit tests (11 tests)
├── examples/
│   └── sample.md             # Sample files
├── docs/
│   ├── USAGE.md              # Usage guide
│   └── DESIGN.md             # Design documentation
├── pyproject.toml            # Project configuration
└── README.md                 # Main documentation
```

## Supported Markdown Elements
- ✅ Headings (h1-h6)
- ✅ Paragraphs and text styles (bold, italic, code, strikethrough)
- ✅ Code blocks (50+ languages)
- ✅ Lists (ordered and unordered)
- ✅ Images (local mode)
- ✅ Blockquotes
- ⏸️ Tables (to be implemented)
- ⏸️ Math formulas (to be implemented)

## Development Status
✅ **Production Ready** - Core features completed and tested

**Test Coverage**: 11 passed, 1 skipped in 0.40s