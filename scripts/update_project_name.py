#!/usr/bin/env python3
"""
Update all documentation to use 'feishu-doc-tools' instead of 'md-to-feishu'.
"""

import os
import re
from pathlib import Path

PROJECT_DIR = Path("/home/howie/Software/utility/Reference/md-to-feishu")

# Files to exclude (don't update these)
EXCLUDE_FILES = {
    "docs/RENAMING.md",  # Renaming documentation needs old name
    "scripts/update_project_name.py",  # This script
    "scripts/update_docs.py",  # Hardcoded path
    "scripts/update_scripts_epilog.py",  # Hardcoded path
    ".serena",  # Serena memory files
    "PROJECT_INDEX",  # Project index files
}

# Pattern to match project name in text (not paths or technical references)
pattern = r'\bmd-to-feishu\b'
replacement = 'feishu-doc-tools'

# Find all markdown files
md_files = []
for md_file in PROJECT_DIR.rglob("*.md"):
    # Check if file should be excluded
    relative_path = md_file.relative_to(PROJECT_DIR)
    if any(str(relative_path).startswith(excl) for excl in EXCLUDE_FILES):
        continue
    md_files.append(md_file)

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
            print(f"Updated: {md_file.relative_to(PROJECT_DIR)}")
        else:
            print(f"No changes needed: {md_file.relative_to(PROJECT_DIR)}")

    except Exception as e:
        print(f"Error processing {md_file.relative_to(PROJECT_DIR)}: {e}")

print("\nDone!")
