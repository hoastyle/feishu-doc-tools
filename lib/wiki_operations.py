#!/usr/bin/env python3
"""
Wiki Operations - Shared Library

This module provides common operations for Wiki-related scripts:
- list_wiki_tree.py
- download_doc.py
- download_wiki.py

It extracts shared functionality to reduce code duplication and ensure
consistent behavior across all Wiki tools.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Callable
from lib.feishu_api_client import FeishuApiClient

logger = logging.getLogger(__name__)


class WikiOperationsError(Exception):
    """Base exception for Wiki operations errors."""
    pass


class SpaceNotFoundError(WikiOperationsError):
    """Raised when a Wiki space is not found."""
    pass


class PathNotFoundError(WikiOperationsError):
    """Raised when a Wiki path cannot be resolved."""
    pass


class DocumentNotFoundError(WikiOperationsError):
    """Raised when a document cannot be found."""
    pass


def resolve_space_id(
    client: FeishuApiClient,
    space_name: str = None,
    space_id: str = None,
    personal: bool = False,
) -> str:
    """
    Unified Wiki space ID resolution.

    Resolves space ID from one of:
    - Direct space_id parameter
    - space_name lookup
    - personal library (My Library)

    Args:
        client: Feishu API client
        space_name: Wiki space name to look up
        space_id: Direct space ID (takes precedence)
        personal: Use personal library (My Library)

    Returns:
        Resolved space ID

    Raises:
        SpaceNotFoundError: If space cannot be found
        ValueError: If no resolution method is provided
    """
    if space_id:
        logger.debug(f"Using provided space_id: {space_id}")
        return space_id

    if personal:
        root_info = client.get_root_info()
        my_library = root_info.get("my_library", {})
        space_id = my_library.get("space_id")
        if not space_id:
            raise SpaceNotFoundError("Personal library (My Library) not found")
        logger.debug(f"Using personal library space_id: {space_id}")
        return space_id

    if space_name:
        logger.debug(f"Looking up space by name: {space_name}")
        resolved_id = client.find_wiki_space_by_name(space_name)
        if not resolved_id:
            raise SpaceNotFoundError(f"Wiki space not found: {space_name}")
        logger.debug(f"Found space_id: {resolved_id}")
        return resolved_id

    raise ValueError("Must provide one of: space_id, space_name, or personal=True")


def resolve_path_to_node(
    client: FeishuApiClient,
    space_id: str,
    path: str,
) -> Tuple[str, Dict[str, Any]]:
    """
    Unified path resolution to find a Wiki node.

    Resolves a path like "/API/Reference/REST" to its node_token and node info.

    Args:
        client: Feishu API client
        space_id: Wiki space ID
        path: Wiki path (e.g., "/API/Reference/REST")

    Returns:
        Tuple of (node_token, node_info)

    Raises:
        PathNotFoundError: If path cannot be resolved
    """
    logger.debug(f"Resolving path: {path}")

    # Split path into parts
    path_parts = [p for p in path.strip("/").split("/") if p]
    if not path_parts:
        raise PathNotFoundError("Path is empty")

    node_name = path_parts[-1]
    parent_path = "/".join(path_parts[:-1]) if len(path_parts) > 1 else None

    # Resolve parent token if needed
    parent_token = None
    if parent_path:
        parent_token = client.resolve_wiki_path(space_id, parent_path)
        if not parent_token:
            raise PathNotFoundError(f"Parent path not found: {parent_path}")

    # Get node list to find the target
    nodes = client.get_wiki_node_list(space_id, parent_token)
    matching_nodes = [
        n for n in nodes
        if n.get("title") == node_name or n.get("node_token") == node_name
    ]

    if not matching_nodes:
        raise PathNotFoundError(f"Path not found: {path}")

    node = matching_nodes[0]
    node_token = node.get("node_token")

    logger.debug(f"Resolved to node_token: {node_token}, title: {node.get('title')}")
    return node_token, node


def traverse_wiki_tree(
    client: FeishuApiClient,
    space_id: str,
    start_token: str = None,
    max_depth: int = -1,
    callback: Callable[[Dict[str, Any], int], Any] = None,
    depth: int = 0,
) -> List[Dict[str, Any]]:
    """
    Generic Wiki tree traversal with optional callback.

    Traverses the Wiki tree starting from a node (or root), optionally
    calling a callback function for each node.

    Args:
        client: Feishu API client
        space_id: Wiki space ID
        start_token: Starting node token (None for root)
        max_depth: Maximum depth to traverse (-1 for unlimited)
        callback: Function called with (node, depth) for each node
        depth: Current depth (used internally for recursion)

    Returns:
        List of all nodes visited (including children)
    """
    # Check depth limit
    if max_depth >= 0 and depth >= max_depth:
        return []

    # Get nodes at this level
    nodes = client.get_wiki_node_list(space_id, start_token)

    all_nodes = []
    for node in nodes:
        # Call callback if provided
        if callback:
            callback(node, depth)

        all_nodes.append(node)

        # Recurse into children if needed
        node_token = node.get("node_token")
        node_type = node.get("node_type", "")
        raw_has_children = node.get("has_children")

        # Determine if we should recurse
        should_recurse = False
        if node_type == "origin" or node_type == "folder":
            should_recurse = True
        elif raw_has_children:
            should_recurse = True

        if should_recurse and max_depth != 0:
            children = traverse_wiki_tree(
                client,
                space_id,
                node_token,
                max_depth,
                callback,
                depth + 1
            )
            all_nodes.extend(children)

    return all_nodes


def find_document_by_name_recursive(
    client: FeishuApiClient,
    space_id: str,
    doc_name: str,
    start_token: str = None,
) -> List[Dict[str, Any]]:
    """
    Recursively search for documents by name.

    Searches the entire Wiki space for documents matching the given name.

    Args:
        client: Feishu API client
        space_id: Wiki space ID
        doc_name: Document name to search for
        start_token: Starting node token (None for root)

    Returns:
        List of matching nodes (may be empty)
    """
    matching_nodes = []

    def collect_matches(node: Dict[str, Any], depth: int) -> None:
        if node.get("title") == doc_name:
            matching_nodes.append(node)

    traverse_wiki_tree(
        client,
        space_id,
        start_token,
        max_depth=-1,  # Unlimited recursion
        callback=collect_matches
    )

    return matching_nodes


def download_document_node(
    client: FeishuApiClient,
    node: Dict[str, Any],
    output_dir: Path,
    feishu_to_md_func: Callable,
    depth: int = 0,
) -> Tuple[bool, str]:
    """
    Download and save a single document node.

    Args:
        client: Feishu API client
        node: Node information dictionary
        output_dir: Output directory
        feishu_to_md_func: Function to convert Feishu blocks to Markdown
        depth: Current depth (for logging indentation)

    Returns:
        Tuple of (success: bool, status_message: str)
        - success: True if downloaded successfully
        - status_message: "successful", "failed", or "skipped"
    """
    from scripts.download_wiki import sanitize_filename, save_document_to_file, DownloadError

    indent = "  " * depth
    node_title = node.get("title", "untitled")
    node_type = node.get("node_type", "")
    obj_token = node.get("obj_token")

    logger.info(f"{indent}Processing: {node_title} ({node_type})")

    # Skip if not a document
    if node_type not in ["doc", "docx"]:
        logger.info(f"{indent}  Skipping non-document node type: {node_type}")
        return False, "skipped"

    # Validate obj_token
    if not obj_token:
        logger.warning(f"{indent}  ⚠ No obj_token found")
        return False, "skipped"

    try:
        # Get document blocks
        blocks = client.get_all_document_blocks(obj_token)

        if not blocks:
            logger.warning(f"{indent}  ⚠ No blocks found")
            return False, "skipped"

        # Convert to Markdown
        markdown = feishu_to_md_func(blocks)

        # Save to file
        output_file = save_document_to_file(markdown, output_dir, node_title)
        logger.info(f"{indent}  ✓ Saved: {output_file.name}")
        return True, "successful"

    except DownloadError as e:
        logger.error(f"{indent}  ✗ Save failed: {e}")
        return False, "failed"
    except Exception as e:
        logger.error(f"{indent}  ✗ Failed: {e}")
        return False, "failed"


def get_node_type_display(node: Dict[str, Any], children: List[Dict[str, Any]] = None) -> str:
    """
    Determine the display icon for a node based on its type and children.

    Args:
        node: Node information dictionary
        children: Optional list of children (if already fetched)

    Returns:
        Icon string (emoji) for the node
    """
    node_type = node.get("node_type", "")
    raw_has_children = node.get("has_children")

    # Determine if it actually has children
    has_children = children is not None and len(children) > 0

    # Icon based on type and whether it has children
    if node_type == "doc" or node_type == "docx":
        return "📄"
    elif node_type == "folder":
        return "📁" if has_children else "📄"
    elif node_type == "origin":
        return "📂" if has_children else "📄"
    else:
        return "📄" if not has_children else "📂"


def sanitize_filename(name: str) -> str:
    """
    Sanitize filename by removing invalid characters.

    Args:
        name: Original filename

    Returns:
        Sanitized filename
    """
    # Replace invalid characters
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        name = name.replace(char, '_')

    # Remove leading/trailing whitespace and dots
    name = name.strip().strip('.')

    return name or "untitled"
