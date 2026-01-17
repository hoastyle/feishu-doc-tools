#!/usr/bin/env python3
"""
Update all CLI tool epilog examples to use 'uv run python scripts/' instead of 'python scripts/'.
"""

import os
import re
from pathlib import Path

SCRIPTS_DIR = Path("/home/howie/Software/utility/Reference/md-to-feishu/scripts")

# Pattern to match command examples in epilog
pattern = r'python scripts/([^)]*?)\.py'
replacement = r'uv run python scripts/\1.py'

# Find all Python scripts
py_files = list(SCRIPTS_DIR.glob("*.py"))

print(f"Found {len(py_files)} Python scripts to update")

for py_file in py_files:
    try:
        # Read file
        content = py_file.read_text(encoding="utf-8")

        # Replace in epilog examples
        new_content = re.sub(pattern, replacement, content)

        # Write back if changed
        if new_content != content:
            py_file.write_text(new_content, encoding="utf-8")
            print(f"Updated: {py_file.name}")
        else:
            print(f"No changes needed: {py_file.name}")

    except Exception as e:
        print(f"Error processing {py_file.name}: {e}")
