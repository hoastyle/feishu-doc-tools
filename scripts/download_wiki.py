#!/usr/bin/env python3
"""
Batch Download Feishu Wiki Documents

Downloads all documents from a Feishu Wiki space and converts them to Markdown.
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.feishu_api_client import FeishuApiClient
from scripts.feishu_to_md import convert_feishu_to_markdown

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Custom exception for download errors."""
    pass


def save_document_to_file(
    content: str,
    output_dir: Path,
    title: str,
) -> Path:
    """
    Save document content to a file, handling duplicate filenames.

    Args:
        content: Markdown content to save
        output_dir: Output directory
        title: Document title (used as filename)

    Returns:
        Path to the saved file

    Raises:
        DownloadError: If file cannot be saved
    """
    from lib.wiki_operations import sanitize_filename

    filename = sanitize_filename(title) + ".md"
    output_file = output_dir / filename

    # Handle duplicate filenames
    counter = 1
    while output_file.exists():
        filename = f"{sanitize_filename(title)}_{counter}.md"
        output_file = output_dir / filename
        counter += 1

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        return output_file
    except OSError as e:
        raise DownloadError(f"Failed to save file {output_file}: {e}") from e


def download_single_document_node(
    client: FeishuApiClient,
    node: Dict[str, Any],
    output_dir: Path,
    depth: int = 0,
) -> Tuple[bool, str]:
    """
    Download and save a single document node.

    Args:
        client: Feishu API client
        node: Node information dictionary
        output_dir: Output directory
        depth: Current depth (for logging indentation)

    Returns:
        Tuple of (success: bool, status_message: str)
        - success: True if downloaded successfully, False if failed/skipped
        - status_message: "successful", "failed", or "skipped"
    """
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
        markdown = convert_feishu_to_markdown(blocks)

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


def download_wiki_node_non_recursive(
    client: FeishuApiClient,
    space_id: str,
    node_token: str,
    output_dir: Path,
) -> Dict[str, Any]:
    """
    Download wiki nodes non-recursively (only direct children).

    Args:
        client: Feishu API client
        space_id: Wiki space ID
        node_token: Node token (parent node)
        output_dir: Output directory

    Returns:
        Result dictionary with statistics
    """
    result = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
    }

    try:
        # Get node list (children of this node)
        logger.info(f"Fetching children of node {node_token or 'root'}...")
        nodes = client.get_wiki_node_list(space_id, node_token)

        if not nodes:
            logger.info("No children found")
            return result

        logger.info(f"Found {len(nodes)} children")

        for node in nodes:
            result["total"] += 1

            # Use shared download function
            success, status = download_single_document_node(
                client, node, output_dir, depth=0
            )
            result[status] += 1

    except Exception as e:
        logger.error(f"Failed to process node: {e}")
        result["failed"] += 1

    return result


def download_wiki_node(
    client: FeishuApiClient,
    space_id: str,
    node_token: str,
    output_dir: Path,
    depth: int = 0,
    max_depth: int = -1,
) -> Dict[str, Any]:
    """
    Recursively download a wiki node and its children.

    Args:
        client: Feishu API client
        space_id: Wiki space ID
        node_token: Node token
        output_dir: Output directory
        depth: Current depth (for logging)
        max_depth: Maximum recursion depth (-1 for unlimited)

    Returns:
        Result dictionary with statistics
    """
    result = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
    }

    try:
        # Get node list (children of this node)
        indent = "  " * depth
        logger.info(f"{indent}Fetching children of node {node_token or 'root'}...")
        nodes = client.get_wiki_node_list(space_id, node_token)

        if not nodes:
            logger.info(f"{indent}No children found")
            return result

        logger.info(f"{indent}Found {len(nodes)} children")

        for node in nodes:
            result["total"] += 1
            node_type = node.get("node_type", "")
            child_node_token = node.get("node_token")

            # Use shared download function
            success, status = download_single_document_node(
                client, node, output_dir, depth
            )
            result[status] += 1

            # Recursively process children if:
            # 1. Node is not a document (e.g., folder), or
            # 2. Node is a document that can also have children
            # 3. Haven't reached max depth (if max_depth >= 0)
            should_recurse = child_node_token and (node_type not in ["doc", "docx"] or not success)
            depth_allows = (max_depth == -1) or (depth < max_depth)

            if should_recurse and depth_allows:
                child_result = download_wiki_node(
                    client, space_id, child_node_token, output_dir, depth + 1, max_depth
                )
                result["total"] += child_result["total"]
                result["successful"] += child_result["successful"]
                result["failed"] += child_result["failed"]
                result["skipped"] += child_result["skipped"]

    except Exception as e:
        logger.error(f"{'  ' * depth}Failed to process node: {e}")
        result["failed"] += 1

    return result


def download_wiki_space(
    space_id: str,
    output_dir: str,
    parent_token: str = None,
    start_path: str = None,
    space_name: str = None,
    personal: bool = False,
    depth: int = -1,
    app_id: str = None,
    app_secret: str = None,
) -> Dict[str, Any]:
    """
    Download all documents from a Wiki space.

    Args:
        space_id: Wiki space ID
        output_dir: Output directory
        parent_token: Optional parent node token (start from specific node)
        start_path: Optional wiki path to start from (alternative to parent_token)
        space_name: Optional space name (alternative to space_id)
        personal: Use personal knowledge base
        depth: Download depth control (-1=unlimited, 0=direct children, 1=children+1 level, etc.)
        app_id: Optional Feishu app ID
        app_secret: Optional Feishu app secret

    Returns:
        Result dictionary with statistics
    """
    from lib.wiki_operations import resolve_space_id, SpaceNotFoundError

    # Initialize client
    if app_id and app_secret:
        client = FeishuApiClient(app_id, app_secret)
    else:
        client = FeishuApiClient.from_env()

    # Resolve space_id using shared library
    try:
        resolved_space_id = resolve_space_id(
            client=client,
            space_name=space_name,
            space_id=space_id,
            personal=personal
        )
        # Use the resolved space_id if provided space_id was None
        if not space_id:
            space_id = resolved_space_id
    except SpaceNotFoundError as e:
        raise ValueError(str(e))

    # Resolve start_path to parent_token if provided
    if start_path:
        logger.info(f"Resolving start path: {start_path}")
        parent_token = client.resolve_wiki_path(space_id, start_path)
        if not parent_token:
            raise ValueError(f"Path not found: {start_path}")
        logger.info(f"  Resolved to node token: {parent_token}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading Wiki space: {space_id}")
    if start_path or parent_token:
        logger.info(f"Starting from: {start_path or parent_token}")

    # Log depth mode
    if depth == -1:
        logger.info("Depth mode: Unlimited recursion")
    elif depth == 0:
        logger.info("Depth mode: Direct children only (no recursion)")
    else:
        logger.info(f"Depth mode: {depth} level(s) of recursion")

    logger.info(f"Output directory: {output_path}")

    # Start download from root or specified parent
    start_token = parent_token or ""

    if depth == 0:
        # Non-recursive: only download direct children
        result = download_wiki_node_non_recursive(
            client, space_id, start_token, output_path
        )
    else:
        # Recursive with depth control
        result = download_wiki_node(
            client, space_id, start_token, output_path, depth=0, max_depth=depth
        )

    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch download Feishu Wiki documents as Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download entire Wiki space - using short aliases
  uv run python scripts/download_wiki.py -s "产品文档" ./output

  # Download personal knowledge base
  uv run python scripts/download_wiki.py -P ./output

  # Download from specific path (recommended) - using short aliases
  uv run python scripts/download_wiki.py \\
    -s "产品文档" \\
    -S "/API/参考" \\
    ./output

  # Download only direct children (non-recursive)
  uv run python scripts/download_wiki.py \\
    -s "产品文档" \\
    -S "/API" \\
    -r \\
    ./output

  # Using long-form options (also valid)
  uv run python scripts/download_wiki.py \\
    --space-name "产品文档" \\
    --start-path "/API/参考" \\
    --no-recursive \\
    ./output

  # Download from specific node (by token)
  uv run python scripts/download_wiki.py \\
    --space-id 74812***88644 \\
    --parent-token nodcnxxxxx \\
    ./output

  # Enable verbose logging
  uv run python scripts/download_wiki.py -P ./output -v

Short Aliases Summary:
  -s, --space-name: Wiki space name
  -P, --personal: Use personal knowledge base
  -S, --start-path: Start from specific wiki path
  -d, --depth: Download depth control (-1=unlimited, 0=direct children only)
  -v, --verbose: Enable verbose logging
        """,
    )

    parser.add_argument(
        "output_dir",
        help="Output directory for downloaded Markdown files",
    )

    # Space identification arguments
    parser.add_argument(
        "--space-id",
        help="Wiki space ID (alternative to --space-name)",
    )
    parser.add_argument(
        "-s",
        "--space-name",
        help="Wiki space name (recommended)",
    )
    parser.add_argument(
        "-P",
        "--personal",
        action="store_true",
        help="Use personal knowledge base (auto-detects space_id)",
    )

    # Starting point arguments
    parser.add_argument(
        "-S",
        "--start-path",
        help="Start from specific wiki path (e.g., '/API/Reference')",
    )
    parser.add_argument(
        "--parent-token",
        help="Start from specific parent node token (alternative to --start-path)",
    )

    # Download behavior arguments
    parser.add_argument(
        "-d",
        "--depth",
        type=int,
        default=-1,
        help=(
            "Download depth control: "
            "-1 = unlimited recursion (default), "
            "0 = only direct children, "
            "1 = children + 1 level, "
            "2 = children + 2 levels, etc."
        ),
    )

    # Authentication arguments
    parser.add_argument(
        "--app-id",
        help="Feishu app ID (or set FEISHU_APP_ID env var)",
    )
    parser.add_argument(
        "--app-secret",
        help="Feishu app secret (or set FEISHU_APP_SECRET env var)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Validate arguments
    if not args.space_id and not args.space_name and not args.personal:
        parser.error("Must specify --space-id, --space-name, or --personal")

    if args.personal and (args.space_id or args.space_name):
        parser.error("--personal cannot be used with --space-id or --space-name")

    if args.start_path and args.parent_token:
        parser.error("Cannot use both --start-path and --parent-token together")

    # Download wiki
    try:
        result = download_wiki_space(
            space_id=args.space_id,
            output_dir=args.output_dir,
            parent_token=args.parent_token,
            start_path=args.start_path,
            space_name=args.space_name,
            personal=args.personal,
            depth=args.depth,
            app_id=args.app_id,
            app_secret=args.app_secret,
        )

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Download Summary")
        print("=" * 60)
        print(f"Total Nodes:    {result['total']}")
        print(f"✅ Successful:  {result['successful']}")
        print(f"❌ Failed:      {result['failed']}")
        print(f"⏭️  Skipped:     {result['skipped']}")
        print("=" * 60)

        sys.exit(0 if result['failed'] == 0 else 1)

    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
