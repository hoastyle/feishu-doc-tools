"""Building blocks for Feishu notification cards.

This package provides composable building blocks for creating Feishu
interactive cards. All blocks return plain dictionaries following Feishu's
card JSON schema.

Quick Example:
    >>> from notifications.blocks import header, markdown, card
    >>>
    >>> notification_card = card(
    ...     header=header(title="Build Complete", template="green"),
    ...     elements=[markdown("**Status**: ✅ Success")]
    ... )
"""

from notifications.blocks.blocks import (
    Block,
    action_button,
    card,
    collapsible_panel,
    column,
    column_set,
    config_textsize_normal_v2,
    divider,
    header,
    markdown,
    note,
    plain_text,
    text_tag,
)

__all__ = [
    "Block",
    "action_button",
    "card",
    "collapsible_panel",
    "column",
    "column_set",
    "config_textsize_normal_v2",
    "divider",
    "header",
    "markdown",
    "note",
    "plain_text",
    "text_tag",
]
