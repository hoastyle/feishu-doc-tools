#!/usr/bin/env python3
"""
Download Feishu Document as Markdown

Downloads a Feishu document and converts it to Markdown format.
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Tuple

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.feishu_api_client import FeishuApiClient
from scripts.feishu_to_md import convert_feishu_to_markdown

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Custom exception for download errors."""
    pass


def resolve_document_id(
    client: FeishuApiClient,
    space_name: str = None,
    wiki_path: str = None,
    doc_name: str = None,
) -> Tuple[str, str]:
    """
    Resolve document ID from space name and path/name.

    Args:
        client: Feishu API client
        space_name: Wiki space name
        wiki_path: Full path to document (e.g., "/API/Reference/REST API")
        doc_name: Document name to search for (alternative to wiki_path)

    Returns:
        Tuple of (document_id, document_title)

    Raises:
        ValueError: If document cannot be found
    """
    from lib.wiki_operations import resolve_space_id, resolve_path_to_node, find_document_by_name_recursive, SpaceNotFoundError, PathNotFoundError, DocumentNotFoundError

    # Resolve space ID
    logger.info(f"Looking for wiki space: {space_name}")
    try:
        space_id = resolve_space_id(client, space_name=space_name)
    except SpaceNotFoundError as e:
        raise DownloadError(str(e))

    logger.info(f"  Found space ID: {space_id}")

    # Resolve path or search by name
    if wiki_path:
        # Use shared library to resolve path
        logger.info(f"Resolving path: {wiki_path}")
        try:
            node_token, node = resolve_path_to_node(client, space_id, wiki_path)
        except PathNotFoundError as e:
            raise DownloadError(str(e))

    elif doc_name:
        # Use shared library to search by name recursively
        logger.info(f"Searching for document: {doc_name}")
        try:
            node_token, node = find_document_by_name_recursive(client, space_id, doc_name)
        except DocumentNotFoundError as e:
            raise ValueError(
                f"{e}\n"
                f"Try using --wiki-path to specify the full path"
            )
    else:
        raise DownloadError("Must provide either --wiki-path or --doc-name")

    # Extract document ID and title
    obj_token = node.get("obj_token")
    title = node.get("title", "untitled")
    node_type = node.get("node_type", "")

    if not obj_token:
        raise DownloadError(f"Node '{title}' is not a document (type: {node_type})")

    logger.info(f"  Found document: {title}")
    logger.info(f"  Document ID: {obj_token}")

    return obj_token, title


def download_document(
    doc_id: str = None,
    output_path: str = None,
    space_name: str = None,
    wiki_path: str = None,
    doc_name: str = None,
    app_id: str = None,
    app_secret: str = None,
) -> bool:
    """
    Download a Feishu document and save as Markdown.

    Args:
        doc_id: Document ID (direct method)
        output_path: Output file path
        space_name: Wiki space name (used with wiki_path or doc_name)
        wiki_path: Full path to document (alternative to doc_id)
        doc_name: Document name to search (alternative to doc_id)
        app_id: Optional Feishu app ID
        app_secret: Optional Feishu app secret

    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize client
        if app_id and app_secret:
            client = FeishuApiClient(app_id, app_secret)
        else:
            client = FeishuApiClient.from_env()

        # Resolve document ID if using name-based method
        doc_title = None
        if space_name:
            doc_id, doc_title = resolve_document_id(
                client, space_name, wiki_path, doc_name
            )

        if not doc_id:
            raise DownloadError("No document ID provided or resolved")

        logger.info(f"Downloading document: {doc_id}")

        # Get all blocks
        blocks = client.get_all_document_blocks(doc_id)

        if not blocks:
            logger.warning("No blocks found in document")
            return False

        logger.info(f"Retrieved {len(blocks)} blocks")

        # Convert to Markdown
        markdown = convert_feishu_to_markdown(blocks)

        # Determine output path
        if not output_path:
            # Generate filename from title if available
            if doc_title:
                # Sanitize title for filename
                safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in doc_title)
                output_path = f"{safe_title}.md"
            else:
                output_path = f"{doc_id}.md"
            logger.info(f"No output path specified, using: {output_path}")

        # Save to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)

        logger.info(f"Saved to: {output_file}")
        logger.info(f"File size: {len(markdown)} characters")

        return True

    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download Feishu document as Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Method 1: Direct document ID (original method)
  uv run python scripts/download_doc.py doxcnxxxxx output.md

  # Method 2: By space name and full path (recommended) - using short aliases
  uv run python scripts/download_doc.py \\
    -s "产品文档" \\
    -p "/API/参考/REST API" \\
    -o rest_api.md

  # Method 3: By space name and document name (convenient) - using short aliases
  uv run python scripts/download_doc.py \\
    -s "产品文档" \\
    -n "REST API" \\
    -o rest_api.md

  # Auto-generate filename from document title
  uv run python scripts/download_doc.py \\
    -s "产品文档" \\
    -p "/API/参考/REST API"

  # Using long-form options (also valid)
  uv run python scripts/download_doc.py \\
    --space-name "产品文档" \\
    --wiki-path "/API/参考/REST API" \\
    --output-file rest_api.md

  # Enable verbose logging
  uv run python scripts/download_doc.py doxcnxxxxx output.md -v

Short Aliases Summary:
  -s, --space-name: Wiki space name
  -p, --wiki-path: Full path to document
  -n, --doc-name: Document name to search
  -o, --output-file: Output file path
  -v, --verbose: Enable verbose logging
        """,
    )

    # Positional arguments (optional when using name-based method)
    parser.add_argument(
        "doc_id",
        nargs="?",
        help="Document ID (e.g., doxcnxxxxx) - required for Method 1",
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Output Markdown file path - required for Method 1, optional for Method 2/3",
    )

    # Name-based method arguments
    parser.add_argument(
        "-s",
        "--space-name",
        help="Wiki space name (required for Method 2 and 3)",
    )
    parser.add_argument(
        "-p",
        "--wiki-path",
        help="Full path to document (e.g., '/API/Reference/REST API') - for Method 2",
    )
    parser.add_argument(
        "-n",
        "--doc-name",
        help="Document name to search for - for Method 3",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        dest="output_file",
        help="Output file path (alternative to positional output argument)",
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

    # Validate arguments and determine method
    using_method_1 = bool(args.doc_id)
    using_method_2_3 = bool(args.space_name)

    if not using_method_1 and not using_method_2_3:
        parser.error(
            "Must specify either:\n"
            "  Method 1: <doc_id> <output>\n"
            "  Method 2: --space-name + --wiki-path [-o output]\n"
            "  Method 3: --space-name + --doc-name [-o output]"
        )

    if using_method_1 and using_method_2_3:
        parser.error(
            "Cannot use both Method 1 (doc_id) and Method 2/3 (--space-name) together"
        )

    # Validate Method 1
    if using_method_1:
        if not args.output and not args.output_file:
            parser.error("Method 1 requires output file: <doc_id> <output>")

    # Validate Method 2/3
    if using_method_2_3:
        if not args.wiki_path and not args.doc_name:
            parser.error(
                "Must specify either --wiki-path or --doc-name with --space-name"
            )

        if args.wiki_path and args.doc_name:
            parser.error(
                "Cannot use both --wiki-path and --doc-name together"
            )

    # Determine output path
    output_path = args.output_file or args.output

    # Download document
    success = download_document(
        doc_id=args.doc_id,
        output_path=output_path,
        space_name=args.space_name,
        wiki_path=args.wiki_path,
        doc_name=args.doc_name,
        app_id=args.app_id,
        app_secret=args.app_secret,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
