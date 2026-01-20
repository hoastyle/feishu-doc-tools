"""Fluent builder API for constructing Feishu interactive cards.

This module provides a chainable CardBuilder class that makes it easy to
construct complex notification cards using a readable, fluent interface.

Example:
    >>> from notifications.templates.builder import CardBuilder
    >>>
    >>> builder = (CardBuilder()
    ...     .header("Document Modified", status="updated", color="blue")
    ...     .markdown("**File**: path/to/file.md")
    ...     .columns()
    ...         .column("Editor", "Alice", width="auto")
    ...         .column("Time", "2026-01-20", width="auto")
    ...     .end_columns()
    ...     .collapsible("Changes", "- Added section\\n- Fixed typo")
    ...     .build())
    >>>
    >>> card = builder.to_dict()
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from notifications.blocks.blocks import (
    Block,
    card,
    collapsible_panel,
    column,
    column_set,
    config_textsize_normal_v2,
    divider,
    header as make_header,
    markdown as md,
    note as make_note,
    text_tag,
)


class CardTemplate:
    """A card template that can be rendered to a dictionary.

    This class wraps the card structure built by CardBuilder and provides
    a simple interface to convert it to the final JSON structure.
    """

    def __init__(
        self,
        header_config: Optional[Dict[str, Any]] = None,
        elements: Optional[List[Block]] = None,
    ):
        """Initialize card template.

        Args:
            header_config: Dictionary containing header configuration
            elements: List of card elements/blocks
        """
        self.header_config = header_config
        self.elements = elements or []

    def to_dict(self) -> Block:
        """Generate the final card dictionary.

        Returns:
            Dictionary containing the complete Feishu card structure
        """
        hdr = None
        if self.header_config:
            hdr = make_header(**self.header_config)

        cfg = config_textsize_normal_v2()
        return card(elements=self.elements, header=hdr, config=cfg)


class CardBuilder:
    """Fluent builder for creating Feishu card templates.

    The CardBuilder provides a chainable API for constructing card templates
    with multiple blocks. It supports high-level convenience methods for
    common card patterns.

    Example:
        >>> builder = (CardBuilder()
        ...     .header("Task Complete", status="success", color="green")
        ...     .metadata("Task Name", "my-task")
        ...     .metadata("Duration", "5 minutes")
        ...     .columns()
        ...         .column("Group", "backend", width="auto")
        ...         .column("Status", "Done", width="auto")
        ...     .end_columns()
        ...     .collapsible("Details", "Task completed successfully")
        ...     .build())
    """

    def __init__(self):
        """Initialize card builder."""
        self._header_config: Optional[Dict[str, Any]] = None
        self._elements: List[Block] = []
        self._column_stack: List[List[Block]] = []

    def header(
        self,
        title: str,
        *,
        status: Optional[str] = None,
        color: Optional[str] = None,
        subtitle: Optional[str] = None,
    ) -> CardBuilder:
        """Set the card header (only one header per card).

        Args:
            title: Header title text
            status: Optional status tag text (e.g., "running", "success", "failed")
            color: Header color theme. If not provided and status is given,
                   auto-detects color from status
            subtitle: Optional subtitle text

        Returns:
            Self for chaining

        Example:
            >>> builder.header("Task Complete", status="success", color="green")
        """
        text_tag_list = None
        if status:
            if color is None:
                # Auto-detect color from status
                status_color_map = {
                    "running": "wathet",
                    "success": "green",
                    "submitted": "wathet",
                    "completed": "green",
                    "failed": "red",
                    "error": "red",
                    "warning": "orange",
                    "info": "blue",
                    "updated": "blue",
                }
                color = status_color_map.get(status.lower(), "blue")
            text_tag_list = [text_tag(status, color)]

        template_color = color or "blue"

        self._header_config = {
            "title": title,
            "template": template_color,
        }
        if subtitle:
            self._header_config["subtitle"] = subtitle
        if text_tag_list:
            self._header_config["text_tag_list"] = text_tag_list

        return self

    def metadata(self, label: str, value: Any) -> CardBuilder:
        """Add a metadata row (can be called multiple times).

        Args:
            label: Metadata label/key
            value: Metadata value (will be converted to string)

        Returns:
            Self for chaining

        Example:
            >>> builder.metadata("Task Name", "my-task")
            >>> builder.metadata("Duration", "5 minutes")
        """
        self._elements.append(
            md(
                f"**{label}:** {value}",
                text_align="left",
                text_size="normal",
                margin="0px 0px 0px 0px",
            )
        )
        return self

    def markdown(
        self,
        content: str,
        *,
        text_align: str = "left",
        text_size: str = "normal",
    ) -> CardBuilder:
        """Add a markdown block (can be called multiple times).

        Args:
            content: Markdown content text
            text_align: Text alignment ("left", "center", "right")
            text_size: Text size ("normal", "normal_v2", etc.)

        Returns:
            Self for chaining

        Example:
            >>> builder.markdown("## Section Title")
            >>> builder.markdown("Some content here")
        """
        self._elements.append(
            md(
                content,
                text_align=text_align,
                text_size=text_size,
                margin="0px 0px 0px 0px",
            )
        )
        return self

    def divider(self) -> CardBuilder:
        """Add a visual divider/separator line.

        Returns:
            Self for chaining

        Example:
            >>> builder.divider()
        """
        self._elements.append(divider())
        return self

    def note(self, content: str) -> CardBuilder:
        """Add a note block with grey background.

        Args:
            content: Note content text

        Returns:
            Self for chaining

        Example:
            >>> builder.note("This is an important note")
        """
        self._elements.append(make_note(content))
        return self

    def columns(self) -> CardBuilder:
        """Start a column set context.

        After calling this, use .column() to add columns, then .end_columns()
        to finalize the column set.

        Returns:
            Self for chaining

        Example:
            >>> builder.columns()
            ...     .column("Left", "value1")
            ...     .column("Right", "value2")
            ...     .end_columns()
        """
        self._column_stack.append([])
        return self

    def column(
        self,
        label: str,
        value: Optional[Any] = None,
        *,
        width: str = "auto",
        weight: int = 1,
    ) -> CardBuilder:
        """Add a column to the current column set.

        Must be called after .columns() and before .end_columns().

        Args:
            label: Column header/label
            value: Column content (optional, uses label if not provided)
            width: Column width ("auto" or "weighted")
            weight: Weight for "weighted" columns (default: 1)

        Returns:
            Self for chaining

        Raises:
            ValueError: If called without an active column set context

        Example:
            >>> builder.columns()
            ...     .column("Name", "Alice", width="auto")
            ...     .column("Status", "Active", width="auto")
            ...     .end_columns()
        """
        if not self._column_stack:
            raise ValueError(
                "Call .columns() before .column(). "
                "Example: builder.columns().column(...).end_columns()"
            )

        if value is not None:
            col_content = md(
                f"**{label}**\n{value}",
                text_align="center",
                text_size="normal",
                margin="0px 4px 0px 4px" if width == "auto" else "0px 0px 0px 0px",
            )
        else:
            col_content = md(
                label,
                text_align="center",
                text_size="normal",
                margin="0px 4px 0px 4px" if width == "auto" else "0px 0px 0px 0px",
            )

        column_block = column(
            [col_content],
            width=width,
            vertical_spacing="8px",
            horizontal_align="left",
            vertical_align="top",
            weight=weight if width == "weighted" else None,
        )

        self._column_stack[-1].append(column_block)
        return self

    def end_columns(
        self,
        *,
        background_style: str = "grey-100",
        horizontal_spacing: str = "12px",
    ) -> CardBuilder:
        """End the current column set context and add it to elements.

        Args:
            background_style: Background color for the column set
            horizontal_spacing: Space between columns

        Returns:
            Self for chaining

        Raises:
            ValueError: If no column set context is active

        Example:
            >>> builder.columns()
            ...     .column("A", "1")
            ...     .column("B", "2")
            ...     .end_columns()
        """
        if not self._column_stack:
            raise ValueError("No column context to end. Use .columns() first.")

        cols = self._column_stack.pop()
        self._elements.append(
            column_set(
                cols,
                background_style=background_style,
                horizontal_spacing=horizontal_spacing,
                horizontal_align="left",
                margin="0px 0px 0px 0px",
            )
        )
        return self

    def collapsible(
        self,
        title: str,
        content: str,
        *,
        expanded: bool = False,
    ) -> CardBuilder:
        """Add a collapsible panel (can be called multiple times).

        Args:
            title: Panel title text
            content: Panel content (supports markdown)
            expanded: Whether panel is initially expanded (default: False)

        Returns:
            Self for chaining

        Example:
            >>> builder.collapsible("Details", "Task details here", expanded=False)
            >>> builder.collapsible("Logs", "Log output here", expanded=True)
        """
        self._elements.append(
            collapsible_panel(
                f"**{title}**",
                [
                    md(
                        content,
                        text_align="left",
                        text_size="normal",
                        margin="0px 0px 0px 0px",
                    )
                ],
                expanded=expanded,
            )
        )
        return self

    def add_block(self, block: Block) -> CardBuilder:
        """Add a raw block for maximum flexibility.

        This allows you to add any custom block that you've built
        using the blocks module functions directly.

        Args:
            block: Raw block dictionary from blocks module

        Returns:
            Self for chaining

        Example:
            >>> from notifications.blocks import markdown
            >>> builder.add_block(markdown("Custom block"))
        """
        self._elements.append(block)
        return self

    def build(self) -> CardTemplate:
        """Build and return the final template.

        Returns:
            CardTemplate instance ready to be rendered

        Raises:
            ValueError: If column context is still open (forgot end_columns())

        Example:
            >>> template = builder.build()
            >>> card_dict = template.to_dict()
        """
        if self._column_stack:
            raise ValueError(
                f"Unclosed column context! You have {len(self._column_stack)} "
                "open column set(s). Call .end_columns() to close them."
            )

        return CardTemplate(
            header_config=self._header_config,
            elements=self._elements,
        )
