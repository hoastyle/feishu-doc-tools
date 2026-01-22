"""Reusable building blocks for constructing Feishu interactive cards.

This module provides small, composable functions that return block dictionaries
compatible with Feishu's interactive card schema. These blocks can be composed
to build complete notification cards.

All functions return plain dicts following Feishu's card JSON schema.
Reference: https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/card-structure

Example:
    >>> from notifications.blocks import markdown, header, column_set, column
    >>>
    >>> # Create a simple card structure
    >>> card_header = header(title="Document Updated", template="blue")
    >>> content = markdown("**File**: README.md\n**Editor**: Alice")
    >>> card = {
    ...     "header": card_header,
    ...     "elements": [content]
    ... }
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

# Type alias for better documentation
Block = Dict[str, Any]


def markdown(
    content: str,
    *,
    text_align: str = "left",
    text_size: str = "normal",
    margin: str = "0px 0px 0px 0px",
) -> Block:
    """Create a markdown text block.

    Args:
        content: Markdown content string (supports **bold**, *italic*, etc.)
        text_align: Text alignment ("left", "center", "right")
        text_size: Text size ("normal", "heading", "notation")
        margin: CSS-like margin string

    Returns:
        A markdown block dict

    Example:
        >>> markdown("**Important**: File updated successfully")
        {'tag': 'markdown', 'content': '**Important**: File updated successfully', ...}
    """
    return {
        "tag": "markdown",
        "content": content,
        "text_align": text_align,
        "text_size": text_size,
        "margin": margin,
    }


def plain_text(text: str) -> Block:
    """Create a plain text element.

    Args:
        text: Plain text content

    Returns:
        A plain_text block dict

    Example:
        >>> plain_text("Document Title")
        {'tag': 'plain_text', 'content': 'Document Title'}
    """
    return {
        "tag": "plain_text",
        "content": text,
    }


def person(
    user_id: str,
    name: str,
) -> Block:
    """Create a person mention tag (@mention).

    Args:
        user_id: User ID in Feishu system
        name: Display name of the user

    Returns:
        A person block dict

    Example:
        >>> person("ou_7d...", "Alice")
        {'tag': 'person', 'user_id': 'ou_7d...', 'name': {'tag': 'plain_text', 'content': 'Alice'}}
    """
    return {
        "tag": "person",
        "user_id": user_id,
        "name": plain_text(name),
    }


def datetime_element(
    content: str,
    *,
    mode: str = "date",
) -> Block:
    """Create a date/time element block.

    Args:
        content: Date/time string
        mode: Display mode ("date", "time", "datetime")

    Returns:
        A datetime block dict

    Example:
        >>> datetime_element("2026-01-22 18:00:00", mode="datetime")
        {'tag': 'datetime', 'content': '2026-01-22 18:00:00', 'mode': 'datetime'}
    """
    return {
        "tag": "datetime",
        "content": content,
        "mode": mode,
    }


def text_tag(text: str, color: str) -> Block:
    """Create a colored text tag for card headers.

    Args:
        text: Tag text
        color: Tag color ("blue", "green", "red", "yellow", "orange", "grey")

    Returns:
        A text_tag block dict

    Example:
        >>> text_tag("NEW", "green")
        {'tag': 'text_tag', 'text': {'tag': 'plain_text', 'content': 'NEW'}, 'color': 'green'}
    """
    return {
        "tag": "text_tag",
        "text": plain_text(text),
        "color": color,
    }


def header(
    *,
    title: str,
    template: str = "blue",
    subtitle: Optional[str] = None,
    text_tag_list: Optional[List[Block]] = None,
    padding: Optional[str] = None,
) -> Block:
    """Create a card header block.

    Args:
        title: Header title text
        template: Color template ("blue", "wathet", "turquoise", "green",
                                  "yellow", "orange", "red", "carmine", "violet", "purple", "grey")
        subtitle: Optional subtitle text
        text_tag_list: Optional list of text tags
        padding: Optional padding string

    Returns:
        A header block dict

    Example:
        >>> header(title="Build Success", template="green", text_tag_list=[text_tag("v1.2.3", "blue")])
        {'title': {'tag': 'plain_text', 'content': 'Build Success'}, 'template': 'green', ...}
    """
    h: Block = {
        "title": plain_text(title),
        "template": template,
    }
    if subtitle is not None:
        h["subtitle"] = plain_text(subtitle)
    if text_tag_list:
        h["text_tag_list"] = text_tag_list
    if padding is not None:
        h["padding"] = padding
    return h


def divider(margin: str = "0px 0px 0px 0px") -> Block:
    """Create a divider line.

    Args:
        margin: CSS-like margin string

    Returns:
        A divider block dict

    Example:
        >>> divider()
        {'tag': 'hr', 'margin': '0px 0px 0px 0px'}
    """
    return {
        "tag": "hr",
        "margin": margin,
    }


def column(
    elements: Iterable[Block],
    *,
    width: str = "auto",
    vertical_spacing: str = "8px",
    horizontal_align: str = "left",
    vertical_align: str = "top",
    weight: Optional[int] = None,
) -> Block:
    """Create a column block for multi-column layouts.

    Args:
        elements: List of blocks in this column
        width: Column width ("auto", "weighted", or specific value like "200px")
        vertical_spacing: Space between elements
        horizontal_align: Horizontal alignment ("left", "center", "right")
        vertical_align: Vertical alignment ("top", "center", "bottom")
        weight: Optional weight for "weighted" width mode

    Returns:
        A column block dict

    Example:
        >>> column([markdown("**Name**"), markdown("Alice")], width="weighted", weight=1)
        {'tag': 'column', 'width': 'weighted', 'elements': [...], 'weight': 1, ...}
    """
    col: Block = {
        "tag": "column",
        "width": width,
        "elements": list(elements),
        "vertical_spacing": vertical_spacing,
        "horizontal_align": horizontal_align,
        "vertical_align": vertical_align,
    }
    if weight is not None:
        col["weight"] = weight
    return col


def column_set(
    columns: Iterable[Block],
    *,
    background_style: str = "grey-100",
    horizontal_spacing: str = "12px",
    horizontal_align: str = "left",
    margin: str = "0px 0px 0px 0px",
) -> Block:
    """Create a column set wrapper for multiple columns.

    Args:
        columns: List of column blocks
        background_style: Background color/style
        horizontal_spacing: Space between columns
        horizontal_align: Horizontal alignment
        margin: CSS-like margin string

    Returns:
        A column_set block dict

    Example:
        >>> cols = [
        ...     column([markdown("**File**")], width="weighted", weight=1),
        ...     column([markdown("README.md")], width="weighted", weight=2),
        ... ]
        >>> column_set(cols)
        {'tag': 'column_set', 'columns': [...], ...}
    """
    return {
        "tag": "column_set",
        "background_style": background_style,
        "horizontal_spacing": horizontal_spacing,
        "horizontal_align": horizontal_align,
        "columns": list(columns),
        "margin": margin,
    }


def collapsible_panel(
    title_markdown_content: str,
    elements: Iterable[Block],
    *,
    expanded: bool = False,
    background_color: str = "grey-200",
    border_color: str = "grey",
    corner_radius: str = "5px",
    padding: str = "12px 12px 12px 12px",
    vertical_spacing: str = "8px",
) -> Block:
    """Create a collapsible panel with title and content.

    Args:
        title_markdown_content: Markdown content for the title
        elements: List of blocks inside the panel
        expanded: Whether panel is expanded by default
        background_color: Panel background color
        border_color: Border color
        corner_radius: Corner radius
        padding: Panel padding
        vertical_spacing: Vertical spacing between elements

    Returns:
        A collapsible_panel block dict

    Example:
        >>> collapsible_panel(
        ...     "**Details**",
        ...     [markdown("Additional information here")],
        ...     expanded=False
        ... )
        {'tag': 'collapsible_panel', 'header': {...}, 'elements': [...], ...}
    """
    return {
        "tag": "collapsible_panel",
        "header": {
            "title": markdown(title_markdown_content, margin="0px"),
        },
        "elements": list(elements),
        "expanded": expanded,
        "background_color": background_color,
        "border_color": border_color,
        "corner_radius": corner_radius,
        "padding": padding,
        "vertical_spacing": vertical_spacing,
    }


def action_button(
    text: str,
    *,
    url: Optional[str] = None,
    action_type: str = "link",
    button_type: str = "default",
) -> Block:
    """Create an action button.

    Args:
        text: Button text
        url: Optional URL for link buttons
        action_type: Action type ("link", "request", etc.)
        button_type: Button style ("default", "primary", "danger")

    Returns:
        An action button block dict

    Example:
        >>> action_button("View Document", url="https://example.com", button_type="primary")
        {'tag': 'button', 'text': {'tag': 'plain_text', 'content': 'View Document'}, ...}
    """
    button: Block = {
        "tag": "button",
        "text": plain_text(text),
        "type": button_type,
    }
    if url:
        button["url"] = url
    return button


def note(
    elements: Iterable[Block],
    *,
    margin: str = "0px 0px 0px 0px",
) -> Block:
    """Create a note block (gray background, smaller text).

    Args:
        elements: List of blocks (typically markdown) in the note
        margin: CSS-like margin string

    Returns:
        A note block dict

    Example:
        >>> note([markdown("ℹ️ This is an informational note")])
        {'tag': 'note', 'elements': [...], 'margin': '0px 0px 0px 0px'}
    """
    return {
        "tag": "note",
        "elements": list(elements),
        "margin": margin,
    }


def img(
    img_key: str,
    *,
    alt: Optional[str] = None,
    mode: str = "fit_center",
    preview: bool = False,
    title: Optional[str] = None,
) -> Block:
    """Create an image block for displaying images in cards.

    Args:
        img_key: Image file key (must be uploaded to Feishu first)
        alt: Alternative text for accessibility
        mode: Display mode ("crop_center", "fit_center", "full_strip")
        preview: Whether to show preview
        title: Image title

    Returns:
        An image block dict

    Example:
        >>> img("img_v7...", alt="Screenshot", mode="fit_center")
        {'tag': 'img', 'img_key': 'img_v7...', 'alt': {'tag': 'plain_text', 'content': 'Screenshot'}, ...}
    """
    image_block: Block = {
        "tag": "img",
        "img_key": img_key,
        "mode": mode,
        "preview": preview,
    }
    if alt is not None:
        image_block["alt"] = plain_text(alt)
    if title is not None:
        image_block["title"] = plain_text(title)
    return image_block


def progress(
    value: str,
    total: str,
    *,
    color: str = "blue",
) -> Block:
    """Create a progress bar block.

    Args:
        value: Current progress value (e.g., "60")
        total: Total progress value (e.g., "100")
        color: Progress bar color ("blue", "green", "red", "yellow", "grey")

    Returns:
        A progress block dict

    Example:
        >>> progress("60", "100", color="green")
        {'tag': 'progress', 'value': '60', 'total': '100', 'color': 'green'}
    """
    return {
        "tag": "progress",
        "value": value,
        "total": total,
        "color": color,
    }


def card(
    *,
    header: Optional[Block] = None,
    elements: Iterable[Block],
    config: Optional[Block] = None,
) -> Block:
    """Create a complete interactive card.

    Args:
        header: Optional header block (from header())
        elements: List of content blocks
        config: Optional configuration block

    Returns:
        A complete card dict

    Example:
        >>> card(
        ...     header=header(title="Notification", template="blue"),
        ...     elements=[markdown("**Status**: Success")]
        ... )
        {'header': {...}, 'elements': [...]}
    """
    c: Block = {
        "elements": list(elements),
    }
    if header is not None:
        c["header"] = header
    if config is not None:
        c["config"] = config
    return c


def config_textsize_normal_v2() -> Block:
    """Create a config block for responsive text sizing.

    Returns:
        A config block dict for responsive text

    Example:
        >>> config_textsize_normal_v2()
        {'update_multi': True, 'style': {'text_size': {...}}}
    """
    return {
        "update_multi": True,
        "style": {
            "text_size": {
                "normal_v2": {
                    "default": "normal",
                    "pc": "normal",
                    "mobile": "heading",
                }
            }
        },
    }
