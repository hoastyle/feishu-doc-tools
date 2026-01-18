#!/usr/bin/env python3
"""
List Wiki Knowledge Base Hierarchy Structure

This script displays tree structure of a Wiki space without downloading any content.
Similar to 'tree' command but for Feishu Wiki.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.feishu_api_client import FeishuApiClient

# Setup minimal logging
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def print_tree_with_count(
    nodes: List[Dict[str, Any]], space_id: str, client: FeishuApiClient,
    parent_token: str = None, prefix: str = "", is_last: bool = True,
    current_depth: int = 0, max_depth: int = -1, debug: bool = False
) -> int:
    """
    Recursively print Wiki node tree structure AND count nodes in a single pass.
    This avoids duplicate API calls for fetching children.

    Args:
        nodes: List of nodes to display
        space_id: Wiki space ID
        client: Feishu API client
        parent_token: Parent node token (for recursion)
        prefix: Tree branch prefix
        is_last: Whether this is the last branch
        current_depth: Current recursion depth
        max_depth: Maximum depth to display (-1 for unlimited)
        debug: Print debug information

    Returns:
        Total count of nodes in this subtree (including current nodes)
    """
    if not nodes:
        return 0

    # Check depth limit
    if max_depth >= 0 and current_depth >= max_depth:
        return len(nodes)

    count = len(nodes)

    for i, node in enumerate(nodes):
        is_last_node = (i == len(nodes) - 1)

        # Tree branch characters
        if prefix == "":
            # Root level
            connector = ""
        else:
            connector = "└── " if is_last_node else "├── "

        # Get node info
        node_title = node.get('title', 'Untitled')
        node_type = node.get('node_type', '')
        node_token = node.get('node_token', '')
        obj_token = node.get('obj_token')
        raw_has_children = node.get('has_children')

        # Debug output
        if debug:
            print(f"[DEBUG] {node_title}: type={node_type}, has_children={raw_has_children}, obj_token={obj_token}")

        # Fetch children once (OPTIMIZATION: same logic as before, but reused for counting)
        children = None
        if node_type == 'origin':
            try:
                children = client.get_wiki_node_list(space_id, node_token)
            except Exception as e:
                logger.error(f"Error fetching children for {node_title}: {e}")
                children = None
        elif raw_has_children:
            try:
                children = client.get_wiki_node_list(space_id, node_token)
            except Exception as e:
                logger.error(f"Error fetching children for {node_title}: {e}")
                children = None

        # Determine icon based on whether it actually has children
        has_children = children is not None and len(children) > 0

        if debug:
            print(f"[DEBUG] {node_title}: actual_children={len(children) if children else 0}, is_doc={not has_children}")

        # Icon based on type and whether it has children
        if node_type == 'doc' or node_type == 'docx':
            icon = '📄'
        elif node_type == 'folder':
            icon = '📁' if has_children else '📄'
        elif node_type == 'origin':
            # origin type: 📂 if has children, 📄 if it's a leaf document
            icon = '📂' if has_children else '📄'
        else:
            icon = '📄' if not has_children else '📂'

        # Print current node
        print(f"{prefix}{connector}{icon} {node_title}")

        # Recursively display children and count them if we have any
        if has_children and children:
            # Build prefix for children
            if prefix == "":
                child_prefix = "    "
            else:
                child_prefix = prefix + ("    " if is_last_node else "│   ")

            child_count = print_tree_with_count(
                children,
                space_id,
                client,
                node_token,
                child_prefix,
                True,
                current_depth + 1,
                max_depth,
                debug
            )
            count += child_count

    return count


def list_wiki_tree(client: FeishuApiClient, space_name: str = None,
                   space_id: str = None, start_path: str = None, max_depth: int = -1,
                   debug: bool = False):
    """
    List Wiki space as a tree structure.

    Args:
        client: Feishu API client
        space_name: Wiki space name
        space_id: Wiki space ID
        start_path: Starting path (optional)
        max_depth: Maximum depth to display (-1 for unlimited, 0 for root only, 1 for 1 level, etc.)
        debug: Print debug information
    """
    # Resolve space ID using shared library
    from lib.wiki_operations import resolve_space_id, SpaceNotFoundError

    try:
        space_id = resolve_space_id(
            client=client,
            space_name=space_name,
            space_id=space_id,
            personal=(space_name is None and space_id is None)
        )
    except SpaceNotFoundError as e:
        print(f"❌ {e}")
        return

    # Resolve starting node
    parent_token = None
    if start_path:
        parent_token = client.resolve_wiki_path(space_id, start_path)
        if not parent_token:
            print(f"❌ Path not found: {start_path}")
            return
        print(f"📂 Path: {start_path}")
    else:
        print(f"📚 Wiki Space: {space_name or space_id}")

    # Get root nodes
    start_time = time.time()
    nodes = client.get_wiki_node_list(space_id, parent_token)
    fetch_time = time.time() - start_time

    if debug:
        print(f"[DEBUG] Got {len(nodes)} root nodes")
        for node in nodes:
            print(f"[DEBUG]   - {node.get('title')}: type={node.get('node_type')}, has_children={node.get('has_children')}, obj_token={node.get('obj_token')}")

    if not nodes:
        print("📭 (empty)")
        return

    # Print tree
    print(f"\n🌳 Tree Structure:")
    print("=" * 60)
    tree_start = time.time()
    total = print_tree_with_count(nodes, space_id, client, parent_token, "", True, 0, max_depth, debug)
    tree_time = time.time() - tree_start
    print("=" * 60)

    # Statistics
    print(f"\n📊 Total Nodes (shown): {total}")
    print(f"⏱️  API Call Time: {fetch_time:.2f}s")
    print(f"⏱️  Tree Build Time: {tree_time:.2f}s")
    print(f"⏱️  Total Time: {(time.time() - start_time):.2f}s")

    if max_depth >= 0:
        print(f"📏 Depth Limit: {max_depth} level(s)")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="List Wiki knowledge base hierarchy structure (tree view)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List personal knowledge base (unlimited depth)
  uv run python scripts/list_wiki_tree.py --personal

  # List only 1 level depth
  uv run python scripts/list_wiki_tree.py -s "产品文档" -d 1

  # List 2 levels deep
  uv run python scripts/list_wiki_tree.py -s "产品文档" -d 2

  # List from specific path
  uv run python scripts/list_wiki_tree.py -s "产品文档" -S "/API" -d 1

  # Use space ID directly
  uv run python scripts/list_wiki_tree.py --space-id 74812***88644

  # Debug mode to see raw node data
  uv run python scripts/list_wiki_tree.py -s "产品文档" --debug
    """
    )

    # Space identification
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--space-name", help="Wiki space name")
    group.add_argument("--space-id", help="Wiki space ID")
    group.add_argument("-P", "--personal", action="store_true", help="Use personal knowledge base")

    # Optional arguments
    parser.add_argument("-S", "--start-path", help="Start from specific path (e.g., '/API')")
    parser.add_argument("-d", "--depth", type=int, default=-1,
                       help="[NEW] Max depth to display: -1=unlimited (default), 0=root only, 1=1 level, 2=2 levels, etc.")
    parser.add_argument("--debug", action="store_true", help="Print debug information (raw node data)")
    parser.add_argument("--app-id", help="Feishu app ID (or set FEISHU_APP_ID env var)")
    parser.add_argument("--app-secret", help="Feishu app secret (or set FEISHU_APP_SECRET env var)")

    args = parser.parse_args()

    try:
        # Initialize client
        if args.app_id and args.app_secret:
            client = FeishuApiClient(args.app_id, args.app_secret)
        else:
            client = FeishuApiClient.from_env()

        # List tree
        list_wiki_tree(
            client=client,
            space_name=args.space_name if not args.personal else None,
            space_id=args.space_id,
            start_path=args.start_path,
            max_depth=args.depth,
            debug=args.debug
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
