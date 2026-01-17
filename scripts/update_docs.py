#!/usr/bin/env python3
"""
Update all documentation to use uv run python instead of python.
"""

import os
import re
from pathlib import Path

DOCS_DIR = Path("/home/howie/Software/utility/Reference/md-to-feishu/docs")

# Pattern to match command examples
pattern = r'python scripts/([^)]+?)\.py'
replacement = r'uv run python scripts/\1.py'

# Find all markdown files
md_files = list(DOCS_DIR.glob("*.md"))

print(f"Found {len(md_files)} markdown files to update")

for md_file in md_files:
    try:
        # Read file
        content = md_file.read_text(encoding="utf-8")

        # Replace all occurrences
        new_content = re.sub(pattern, replacement, content)

        # Write back if changed
        if new_content != content:
            md_file.write_text(new_content, encoding="utf-8")
            print(f"Updated: {md_file.name}")
        else:
            print(f"No changes needed: {md_file.name}")

    except Exception as e:
        print(f"Error processing {md_file.name}: {e}")
