#!/usr/bin/env python3
"""
Create a new document in a Feishu Wiki space (knowledge base).

This script creates a new wiki node in a specified wiki space and uploads markdown content to it.

Usage Examples:
    # List available wiki spaces
    python scripts/create_wiki_doc.py --list-spaces

    # Create in "个人知识库" (default)
    python scripts/create_wiki_doc.py README.md

    # Create with custom title in specific space
    python scripts/create_wiki_doc.py README.md --title "User Guide" --space-id 7516222021840306180

    # Create as child of another node
    python scripts/create_wiki_doc.py README.md --parent-token nodcnxxxxx

Features:
    - Lists available wiki spaces
    - Creates wiki nodes in any accessible space
    - Uploads markdown content with images
    - Supports creating at root or as child node
    - Detailed progress reporting

Wiki Spaces:
    - Use --list-spaces to see all available spaces
    - Common spaces:
      - My Library (my_library): Personal document library
      - Team spaces: Shared knowledge bases
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.feishu_api_client import FeishuApiClient, FeishuApiClientError

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def list_wiki_spaces(client):
    """List all available wiki spaces."""
    try:
        spaces = client.get_all_wiki_spaces()

        print("=" * 70)
        print("📚 可用的知识空间 (Wiki Spaces)")
        print("=" * 70)

        for i, space in enumerate(spaces, 1):
            name = space.get("name", "Unknown")
            space_id = space.get("space_id")
            space_type = space.get("space_type", "unknown")
            visibility = space.get("visibility", "unknown")
            desc = space.get("description", "")

            print(f"\n{i}. {name}")
            print(f"   Space ID: {space_id}")
            print(f"   Type: {space_type}")
            print(f"   Visibility: {visibility}")
            if desc:
                print(f"   Description: {desc}")

        print("\n" + "=" * 70)
        print("💡 使用方法:")
        print(f'   python scripts/create_wiki_doc.py README.md --space-id {spaces[0]["space_id"]}')
        print("=" * 70)

        return 0

    except FeishuApiClientError as e:
        logger.error(f"Failed to list wiki spaces: {e}")
        return 1


def create_wiki_document(
    client,
    md_file: Path,
    space_id: str,
    title: str = None,
    parent_node_token: str = None
):
    """Create a wiki document from markdown file."""
    try:
        # Get title from filename if not provided
        if not title:
            title = md_file.stem

        logger.info(f"Creating wiki document from: {md_file}")

        # Step 1: Create wiki node
        logger.info(f"Step 1: Creating wiki node in space {space_id}...")
        node_result = client.create_wiki_node(
            space_id=space_id,
            title=title,
            parent_node_token=parent_node_token
        )

        doc_id = node_result["document_id"]
        node_token = node_result["node_token"]
        logger.info(f"  ✓ Wiki node created: {node_token}")
        logger.info(f"  ✓ Document ID: {doc_id}")

        # Step 2: Upload markdown content
        logger.info(f"Step 2: Uploading markdown content...")

        # Import here to avoid circular dependency
        from lib.feishu_api_client import upload_markdown_to_feishu

        upload_result = upload_markdown_to_feishu(
            md_file=str(md_file),
            doc_id=doc_id,
            app_id=client.app_id,
            app_secret=client.app_secret
        )

        # Print results
        print("\n" + "=" * 70)
        print("✅ Wiki Document Created Successfully")
        print("=" * 70)
        print(f"Title:           {title}")
        print(f"Space ID:        {space_id}")
        print(f"Node Token:      {node_result['node_token']}")
        print(f"Document ID:     {doc_id}")
        print(f"Wiki URL:        {node_result['url']}")
        print(f"Doc URL:         https://feishu.cn/docx/{doc_id}")
        print(f"Blocks:          {upload_result.get('total_blocks', 0)}")
        print(f"Images:          {upload_result.get('total_images', 0)}")
        print(f"Batches:         {upload_result.get('total_batches', 0)}")
        print("=" * 70)

        return {
            "success": True,
            "title": title,
            "space_id": space_id,
            "node_token": node_result["node_token"],
            "document_id": doc_id,
            "wiki_url": node_result["url"],
            "doc_url": f"https://feishu.cn/docx/{doc_id}",
            **upload_result
        }

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return {"success": False, "error": str(e)}
    except FeishuApiClientError as e:
        logger.error(f"API Error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a new document in a Feishu Wiki space",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available wiki spaces
  python scripts/create_wiki_doc.py --list-spaces

  # Create in personal knowledge base (use space_id)
  python scripts/create_wiki_doc.py README.md --space-id 7516222021840306180

  # Create with custom title
  python scripts/create_wiki_doc.py docs/guide.md --title "User Guide" --space-id 7516222021840306180

  # Create as child of another node
  python scripts/create_wiki_doc.py README.md --parent-token nodcnxxxxx --space-id 7516222021840306180
        """,
    )

    parser.add_argument("md_file", nargs="?", type=Path, help="Path to markdown file to upload")

    parser.add_argument(
        "--list-spaces",
        action="store_true",
        help="List all available wiki spaces and exit"
    )

    parser.add_argument(
        "--space-id",
        type=str,
        default=None,
        help="Target wiki space ID (use --list-spaces to see available spaces)"
    )

    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Document title (default: filename without extension)"
    )

    parser.add_argument(
        "--parent-token",
        type=str,
        default=None,
        help="Parent node token (creates at root if not provided)"
    )

    parser.add_argument(
        "--app-id", type=str, default=None, help="Feishu app ID (or set FEISHU_APP_ID env var)"
    )

    parser.add_argument(
        "--app-secret",
        type=str,
        default=None,
        help="Feishu app secret (or set FEISHU_APP_SECRET env var)"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output (debug logging)"
    )

    args = parser.parse_args()

    # Enable debug logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize client
    try:
        if args.app_id and args.app_secret:
            client = FeishuApiClient(args.app_id, args.app_secret)
        else:
            client = FeishuApiClient.from_env()
    except FeishuApiClientError as e:
        logger.error(f"Failed to initialize client: {e}")
        return 1

    # Handle --list-spaces
    if args.list_spaces:
        return list_wiki_spaces(client)

    # Validate md_file
    if not args.md_file:
        parser.error("md_file is required (unless using --list-spaces)")
        return 1

    if not args.md_file.exists():
        logger.error(f"File not found: {args.md_file}")
        return 1

    if not args.md_file.is_file():
        logger.error(f"Not a file: {args.md_file}")
        return 1

    if args.md_file.suffix.lower() != ".md":
        logger.warning(f"File extension is not .md: {args.md_file}")

    # Validate space_id
    if not args.space_id:
        logger.error("--space-id is required. Use --list-spaces to see available spaces.")
        return 1

    # Create wiki document
    result = create_wiki_document(
        client=client,
        md_file=args.md_file,
        space_id=args.space_id,
        title=args.title,
        parent_node_token=args.parent_token
    )

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
