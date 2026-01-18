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
from typing import Dict, Any, List

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.feishu_api_client import FeishuApiClient
from scripts.feishu_to_md import convert_feishu_to_markdown

logger = logging.getLogger(__name__)


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
    name = name.strip(). strip('.')

    return name or "untitled"


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
            node_title = node.get("title", "untitled")
            node_type = node.get("node_type", "")
            obj_token = node.get("obj_token")

            logger.info(f"Processing: {node_title} ({node_type})")

            # Skip if not a document
            if node_type not in ["doc", "docx"]:
                logger.info(f"  Skipping non-document node type: {node_type}")
                result["skipped"] += 1
                continue

            # Download document
            if obj_token:
                try:
                    # Get document blocks
                    blocks = client.get_all_document_blocks(obj_token)

                    if blocks:
                        # Convert to Markdown
                        markdown = convert_feishu_to_markdown(blocks)

                        # Save to file
                        filename = sanitize_filename(node_title) + ".md"
                        output_file = output_dir / filename

                        # Handle duplicate filenames
                        counter = 1
                        while output_file.exists():
                            filename = f"{sanitize_filename(node_title)}_{counter}.md"
                            output_file = output_dir / filename
                            counter += 1

                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(markdown)

                        logger.info(f"  ✓ Saved: {output_file.name}")
                        result["successful"] += 1
                    else:
                        logger.warning(f"  ⚠ No blocks found")
                        result["skipped"] += 1

                except Exception as e:
                    logger.error(f"  ✗ Failed: {e}")
                    result["failed"] += 1
            else:
                logger.warning(f"  ⚠ No obj_token found")
                result["skipped"] += 1

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
) -> Dict[str, Any]:
    """
    Recursively download a wiki node and its children.

    Args:
        client: Feishu API client
        space_id: Wiki space ID
        node_token: Node token
        output_dir: Output directory
        depth: Current depth (for logging)

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
        logger.info(f"{'  ' * depth}Fetching children of node {node_token}...")
        nodes = client.get_wiki_node_list(space_id, node_token)

        if not nodes:
            logger.info(f"{'  ' * depth}No children found")
            return result

        logger.info(f"{'  ' * depth}Found {len(nodes)} children")

        for node in nodes:
            result["total"] += 1
            node_title = node.get("title", "untitled")
            node_type = node.get("node_type", "")
            child_node_token = node.get("node_token")
            obj_token = node.get("obj_token")  # Document ID

            logger.info(f"{'  ' * depth}Processing: {node_title} ({node_type})")

            # Skip if not a document
            if node_type != "doc" and node_type != "docx":
                logger.info(f"{'  ' * depth}  Skipping non-document node type: {node_type}")
                result["skipped"] += 1

                # Still recursively process children
                if child_node_token:
                    child_result = download_wiki_node(
                        client, space_id, child_node_token, output_dir, depth + 1
                    )
                    result["total"] += child_result["total"]
                    result["successful"] += child_result["successful"]
                    result["failed"] += child_result["failed"]
                    result["skipped"] += child_result["skipped"]
                continue

            # Download document
            if obj_token:
                try:
                    # Get document blocks
                    blocks = client.get_all_document_blocks(obj_token)

                    if blocks:
                        # Convert to Markdown
                        markdown = convert_feishu_to_markdown(blocks)

                        # Save to file
                        filename = sanitize_filename(node_title) + ".md"
                        output_file = output_dir / filename

                        # Handle duplicate filenames
                        counter = 1
                        while output_file.exists():
                            filename = f"{sanitize_filename(node_title)}_{counter}.md"
                            output_file = output_dir / filename
                            counter += 1

                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(markdown)

                        logger.info(f"{'  ' * depth}  ✓ Saved: {output_file.name}")
                        result["successful"] += 1
                    else:
                        logger.warning(f"{'  ' * depth}  ⚠ No blocks found")
                        result["skipped"] += 1

                except Exception as e:
                    logger.error(f"{'  ' * depth}  ✗ Failed: {e}")
                    result["failed"] += 1

            # Recursively process children
            if child_node_token:
                child_result = download_wiki_node(
                    client, space_id, child_node_token, output_dir, depth + 1
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
    recursive: bool = True,
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
        recursive: Whether to recursively download child nodes (default True)
        app_id: Optional Feishu app ID
        app_secret: Optional Feishu app secret

    Returns:
        Result dictionary with statistics
    """
    # Initialize client
    if app_id and app_secret:
        client = FeishuApiClient(app_id, app_secret)
    else:
        client = FeishuApiClient.from_env()

    # Resolve space_id if space_name provided
    if space_name:
        logger.info(f"Looking for wiki space named: {space_name}")
        space_id = client.find_wiki_space_by_name(space_name)
        if not space_id:
            raise ValueError(f"Wiki space not found: {space_name}")
        logger.info(f"  Found space ID: {space_id}")

    # Auto-detect personal space if requested
    if personal:
        logger.info("Auto-detecting '个人知识库' space...")
        all_spaces = client.get_all_wiki_spaces()
        personal_space = None
        for space in all_spaces:
            if space.get("name") == "个人知识库":
                personal_space = space
                break

        if not personal_space:
            raise ValueError("Personal knowledge base not found")

        space_id = personal_space.get("space_id")
        logger.info(f"  ✓ Detected: {personal_space.get('name')} (space_id: {space_id})")

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
    logger.info(f"Recursive mode: {'enabled' if recursive else 'disabled'}")
    logger.info(f"Output directory: {output_path}")

    # Start download from root or specified parent
    start_token = parent_token or ""

    if recursive:
        result = download_wiki_node(client, space_id, start_token, output_path, depth=0)
    else:
        # Non-recursive: only download direct children
        result = download_wiki_node_non_recursive(
            client, space_id, start_token, output_path
        )

    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch download Feishu Wiki documents as Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download entire Wiki space
  uv run python scripts/download_wiki.py --space-name "产品文档" ./output

  # Download personal knowledge base
  uv run python scripts/download_wiki.py --personal ./output

  # Download from specific path (recommended)
  uv run python scripts/download_wiki.py \\
    --space-name "产品文档" \\
    --start-path "/API/参考" \\
    ./output

  # Download only direct children (non-recursive)
  uv run python scripts/download_wiki.py \\
    --space-name "产品文档" \\
    --start-path "/API" \\
    --no-recursive \\
    ./output

  # Download from specific node (by token)
  uv run python scripts/download_wiki.py \\
    --space-id 74812***88644 \\
    --parent-token nodcnxxxxx \\
    ./output

  # Enable verbose logging
  uv run python scripts/download_wiki.py --personal ./output -v
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
        "--space-name",
        help="Wiki space name (recommended)",
    )
    parser.add_argument(
        "--personal",
        action="store_true",
        help="Use personal knowledge base (auto-detects space_id)",
    )

    # Starting point arguments
    parser.add_argument(
        "--start-path",
        help="Start from specific wiki path (e.g., '/API/Reference')",
    )
    parser.add_argument(
        "--parent-token",
        help="Start from specific parent node token (alternative to --start-path)",
    )

    # Download behavior arguments
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        default=True,
        help="Disable recursive download (only download direct children)",
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
            recursive=args.recursive,
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
