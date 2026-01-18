#!/usr/bin/env python3
"""
Feishu Document to Markdown Converter

Converts Feishu document blocks to Markdown format.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# Feishu block type constants
BLOCK_TYPE_PAGE = 1
BLOCK_TYPE_TEXT = 2
BLOCK_TYPE_HEADING1 = 3
BLOCK_TYPE_HEADING2 = 4
BLOCK_TYPE_HEADING3 = 5
BLOCK_TYPE_HEADING4 = 6
BLOCK_TYPE_HEADING5 = 7
BLOCK_TYPE_HEADING6 = 8
BLOCK_TYPE_HEADING7 = 9
BLOCK_TYPE_HEADING8 = 10
BLOCK_TYPE_HEADING9 = 11
BLOCK_TYPE_BULLET = 12
BLOCK_TYPE_ORDERED = 13
BLOCK_TYPE_CODE = 15
BLOCK_TYPE_QUOTE = 17
BLOCK_TYPE_TODO = 19
BLOCK_TYPE_IMAGE = 27
BLOCK_TYPE_TABLE = 31
BLOCK_TYPE_TABLE_CELL = 32
BLOCK_TYPE_VIEW = 33
BLOCK_TYPE_DIVIDER = 22


# Language code mapping (Feishu code -> Markdown identifier)
LANGUAGE_MAP = {
    1: "text",       # PlainText
    2: "abap",       # ABAP
    7: "bash",       # Bash
    8: "csharp",     # CSharp
    9: "cpp",        # C++
    10: "c",         # C
    12: "css",       # CSS
    15: "dart",      # Dart
    18: "dockerfile",  # Dockerfile
    22: "go",        # Go
    24: "html",      # HTML
    28: "json",      # JSON
    29: "java",      # Java
    30: "javascript",  # JavaScript
    32: "kotlin",    # Kotlin
    33: "latex",     # LaTeX
    36: "lua",       # Lua
    37: "matlab",    # MATLAB
    39: "markdown",  # Markdown
    43: "php",       # PHP
    49: "python",    # Python
    50: "r",         # R
    52: "ruby",      # Ruby
    53: "rust",      # Rust
    56: "sql",       # SQL
    57: "scala",     # Scala
    60: "shell",     # Shell
    61: "swift",     # Swift
    63: "typescript",  # TypeScript
    66: "xml",       # XML
    67: "yaml",      # YAML
}


class FeishuToMarkdownConverter:
    """Convert Feishu document blocks to Markdown format."""

    def __init__(self):
        """Initialize converter."""
        self.markdown_lines = []
        self.list_stack = []  # Track nested list levels
        self.in_table = False
        self.table_data = []

    def convert(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Convert Feishu blocks to Markdown.

        Args:
            blocks: List of Feishu blocks

        Returns:
            Markdown string
        """
        self.markdown_lines = []
        self.list_stack = []
        self.in_table = False
        self.table_data = []

        logger.info(f"Converting {len(blocks)} blocks to Markdown")

        # Build block index for quick lookup
        block_index = {block["block_id"]: block for block in blocks}

        # Find root blocks (no parent or parent is document)
        root_blocks = [
            block for block in blocks
            if not block.get("parent_id") or block.get("parent_id") == ""
        ]

        # Process root blocks
        for block in root_blocks:
            self._process_block(block, block_index, level=0)

        markdown = "\n".join(self.markdown_lines)
        logger.info(f"Generated {len(self.markdown_lines)} lines of Markdown")

        return markdown

    def _process_block(
        self,
        block: Dict[str, Any],
        block_index: Dict[str, Dict[str, Any]],
        level: int = 0,
    ):
        """Process a single block and its children."""
        block_type = block.get("block_type")
        block_id = block.get("block_id")

        logger.debug(f"Processing block {block_id}, type {block_type}, level {level}")

        # Handle different block types
        if block_type == BLOCK_TYPE_PAGE:
            self._process_page(block)
        elif BLOCK_TYPE_HEADING1 <= block_type <= BLOCK_TYPE_HEADING9:
            self._process_heading(block, block_type)
        elif block_type == BLOCK_TYPE_TEXT:
            self._process_text(block)
        elif block_type == BLOCK_TYPE_CODE:
            self._process_code(block)
        elif block_type == BLOCK_TYPE_BULLET:
            self._process_bullet(block, level)
        elif block_type == BLOCK_TYPE_ORDERED:
            self._process_ordered(block, level)
        elif block_type == BLOCK_TYPE_QUOTE:
            self._process_quote(block)
        elif block_type == BLOCK_TYPE_TODO:
            self._process_todo(block)
        elif block_type == BLOCK_TYPE_IMAGE:
            self._process_image(block)
        elif block_type == BLOCK_TYPE_TABLE:
            self._process_table(block, block_index)
        elif block_type == BLOCK_TYPE_DIVIDER:
            self._process_divider()
        else:
            logger.warning(f"Unsupported block type: {block_type}")

        # Process children (except for table cells, handled separately)
        if block_type != BLOCK_TYPE_TABLE and block_type != BLOCK_TYPE_TABLE_CELL:
            children_ids = block.get("children", [])
            for child_id in children_ids:
                child_block = block_index.get(child_id)
                if child_block:
                    self._process_block(child_block, block_index, level + 1)

    def _process_page(self, block: Dict[str, Any]):
        """Process page block (document title)."""
        page_data = block.get("page", {})
        elements = page_data.get("elements", [])
        title = self._extract_text_from_elements(elements)
        if title:
            self.markdown_lines.append(f"# {title}")
            self.markdown_lines.append("")

    def _process_heading(self, block: Dict[str, Any], block_type: int):
        """Process heading block."""
        level = block_type - BLOCK_TYPE_HEADING1 + 1
        heading_key = f"heading{level}"
        heading_data = block.get(heading_key, {})
        elements = heading_data.get("elements", [])
        text = self._extract_text_from_elements(elements)

        if text:
            self.markdown_lines.append(f"{'#' * level} {text}")
            self.markdown_lines.append("")

    def _process_text(self, block: Dict[str, Any]):
        """Process text block."""
        text_data = block.get("text", {})
        elements = text_data.get("elements", [])
        text = self._extract_text_from_elements(elements)

        if text:
            self.markdown_lines.append(text)
            self.markdown_lines.append("")

    def _process_code(self, block: Dict[str, Any]):
        """Process code block."""
        code_data = block.get("code", {})
        language_code = code_data.get("language", 1)
        code = code_data.get("content", "")

        # Map Feishu language code to Markdown identifier
        language = LANGUAGE_MAP.get(language_code, "text")

        self.markdown_lines.append(f"```{language}")
        if code:
            self.markdown_lines.append(code)
        self.markdown_lines.append("```")
        self.markdown_lines.append("")

    def _process_bullet(self, block: Dict[str, Any], level: int):
        """Process bullet list item."""
        bullet_data = block.get("bullet", {})
        elements = bullet_data.get("elements", [])
        text = self._extract_text_from_elements(elements)

        if text:
            indent = "  " * level
            self.markdown_lines.append(f"{indent}- {text}")

    def _process_ordered(self, block: Dict[str, Any], level: int):
        """Process ordered list item."""
        ordered_data = block.get("ordered", {})
        elements = ordered_data.get("elements", [])
        text = self._extract_text_from_elements(elements)

        if text:
            indent = "  " * level
            self.markdown_lines.append(f"{indent}1. {text}")

    def _process_quote(self, block: Dict[str, Any]):
        """Process quote block."""
        quote_data = block.get("quote", {})
        elements = quote_data.get("elements", [])
        text = self._extract_text_from_elements(elements)

        if text:
            self.markdown_lines.append(f"> {text}")
            self.markdown_lines.append("")

    def _process_todo(self, block: Dict[str, Any]):
        """Process todo block."""
        todo_data = block.get("todo", {})
        elements = todo_data.get("elements", [])
        checked = todo_data.get("done", False)
        text = self._extract_text_from_elements(elements)

        if text:
            checkbox = "[x]" if checked else "[ ]"
            self.markdown_lines.append(f"- {checkbox} {text}")

    def _process_image(self, block: Dict[str, Any]):
        """Process image block."""
        # Image handling - placeholder for now
        # In a full implementation, you'd download the image using the token
        self.markdown_lines.append("![Image](image-placeholder.png)")
        self.markdown_lines.append("")

    def _process_table(self, block: Dict[str, Any], block_index: Dict[str, Dict[str, Any]]):
        """Process table block."""
        table_data = block.get("table", {})
        property_data = table_data.get("property", {})
        row_size = property_data.get("row_size", 0)
        column_size = property_data.get("column_size", 0)

        if row_size == 0 or column_size == 0:
            logger.warning("Table has zero size, skipping")
            return

        # Initialize table matrix
        table_matrix = [["" for _ in range(column_size)] for _ in range(row_size)]

        # Get all table cells
        children_ids = block.get("children", [])
        for cell_id in children_ids:
            cell_block = block_index.get(cell_id)
            if cell_block and cell_block.get("block_type") == BLOCK_TYPE_TABLE_CELL:
                # Extract cell position (from block_id pattern: table_xxx_cell_row_col)
                # This is a simplified approach; actual implementation may vary
                pass  # TODO: Extract cell content and position

        # For now, create a simple table placeholder
        self.markdown_lines.append("| Header 1 | Header 2 |")
        self.markdown_lines.append("|----------|----------|")
        self.markdown_lines.append("| Cell 1   | Cell 2   |")
        self.markdown_lines.append("")

    def _process_divider(self):
        """Process divider block."""
        self.markdown_lines.append("---")
        self.markdown_lines.append("")

    def _extract_text_from_elements(self, elements: List[Dict[str, Any]]) -> str:
        """Extract and format text from text elements."""
        text_parts = []

        for element in elements:
            text_run = element.get("text_run")
            if text_run:
                content = text_run.get("content", "")
                style = text_run.get("text_element_style", {})

                # Apply formatting
                formatted_content = self._apply_text_formatting(content, style)
                text_parts.append(formatted_content)

            # Handle equations
            equation = element.get("equation")
            if equation:
                # Wrap equation in LaTeX delimiters
                text_parts.append(f"${equation}$")

        return "".join(text_parts)

    def _apply_text_formatting(self, text: str, style: Dict[str, Any]) -> str:
        """Apply Markdown formatting based on text style."""
        if not text:
            return text

        # Bold
        if style.get("bold"):
            text = f"**{text}**"

        # Italic
        if style.get("italic"):
            text = f"*{text}*"

        # Inline code
        if style.get("inline_code"):
            text = f"`{text}`"

        # Strikethrough
        if style.get("strikethrough"):
            text = f"~~{text}~~"

        # Underline (Markdown doesn't support underline natively, use HTML)
        if style.get("underline"):
            text = f"<u>{text}</u>"

        # Link
        link = style.get("link", {})
        if link and link.get("url"):
            url = link["url"]
            text = f"[{text}]({url})"

        return text


def convert_feishu_to_markdown(blocks: List[Dict[str, Any]]) -> str:
    """
    Convenience function to convert Feishu blocks to Markdown.

    Args:
        blocks: List of Feishu blocks

    Returns:
        Markdown string
    """
    converter = FeishuToMarkdownConverter()
    return converter.convert(blocks)
