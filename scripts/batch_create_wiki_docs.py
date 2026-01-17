#!/usr/bin/env python3
"""
Batch create Feishu Wiki documents from local folder.

This script uploads all Markdown files from a folder to a Wiki space,
creating them as nodes in the Wiki hierarchy.

Usage:
    # Upload to specific Wiki space (root level)
    python scripts/batch_create_wiki_docs.py ./docs --space-id 74812***88644

    # Upload to personal knowledge base
    python scripts/batch_create_wiki_docs.py ./docs --personal

    # Upload to specific parent node
    python scripts/batch_create_wiki_docs.py ./docs --space-id 74812***88644 --parent nodcnxxxxx

    # Custom file pattern
    python scripts/batch_create_wiki_docs.py ./docs --pattern "*.md"
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.feishu_api_client import FeishuApiClient


logger = logging.getLogger(__name__)


def batch_create_wiki_docs(
    folder_path: str,
    space_id: str,
    parent_token: str = None,
    pattern: str = "*.md",
    app_id: str = None,
    app_secret: str = None,
    dry_run: bool = False,
) -> Dict[str, any]:
    """
    Batch create Wiki documents from a folder.

    Args:
        folder_path: Path to folder with markdown files
        space_id: Wiki space ID
        parent_token: Parent node token (creates at root if not provided)
        pattern: File glob pattern (default: *.md)
        app_id: Feishu app ID
        app_secret: Feishu app secret
        dry_run: If True, scan but don't create

    Returns:
        Dictionary with creation results
    """
    # Initialize client
    if app_id and app_secret:
        client = FeishuApiClient(app_id, app_secret)
    else:
        client = FeishuApiClient.from_env()

    # Find all markdown files
    folder = Path(folder_path)
    if not folder.exists():
        logger.error(f"Folder not found: {folder_path}")
        sys.exit(1)

    markdown_files = list(folder.glob(pattern))
    if not markdown_files:
        logger.warning(f"No files found matching pattern: {pattern}")
        return {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "results": [],
        }

    # Sort files for consistent ordering
    markdown_files = sorted(markdown_files)

    logger.info(f"Found {len(markdown_files)} files to upload to Wiki space {space_id}")

    # Track results
    results = []
    successful = 0
    failed = 0

    for md_file in markdown_files:
        try:
            # Get document title from filename
            title = md_file.stem  # filename without extension

            if dry_run:
                logger.info(f"[DRY RUN] Would create: {title} from {md_file.name}")
                results.append({
                    "file": str(md_file),
                    "title": title,
                    "status": "skipped (dry run)",
                })
                continue

            # Create Wiki node
            logger.info(f"Creating Wiki node: {title} from {md_file.name}")

            node = client.create_wiki_node(
                space_id=space_id,
                title=title,
                parent_node_token=parent_token,
            )

            doc_id = node.get("document_id")
            url = node.get("url")

            # Upload content to the new document
            if doc_id:
                from lib.feishu_api_client import upload_markdown_to_feishu

                logger.info(f"Uploading content to document: {doc_id}")
                upload_result = upload_markdown_to_feishu(
                    md_file=str(md_file),
                    doc_id=doc_id,
                    app_id=app_id,
                    app_secret=app_secret,
                )

                results.append({
                    "file": str(md_file),
                    "title": title,
                    "document_id": doc_id,
                    "url": url,
                    "blocks": upload_result.get("total_blocks", 0),
                    "images": upload_result.get("total_images", 0),
                    "status": "success",
                })
                successful += 1

            else:
                results.append({
                    "file": str(md_file),
                    "title": title,
                    "status": "failed (no document_id)",
                })
                failed += 1

        except Exception as e:
            logger.error(f"Failed to process {md_file.name}: {e}")
            results.append({
                "file": str(md_file),
                "title": md_file.stem,
                "status": f"failed: {str(e)}",
            })
            failed += 1

    return {
        "total_files": len(markdown_files),
        "successful": successful,
        "failed": failed,
        "results": results,
        "space_id": space_id,
        "parent_token": parent_token,
    }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch create Feishu Wiki documents from local folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload all .md files to Wiki space (root level)
  python scripts/batch_create_wiki_docs.py ./docs --space-id 74812***88644

  # Upload to personal knowledge base
  python scripts/batch_create_wiki_docs.py ./docs --personal

  # Upload to specific parent node (subdirectory)
  python scripts/batch_create_wiki_docs.py ./docs --space-id 74812***88644 --parent nodcnxxxxx

  # Custom file pattern
  python scripts/batch_create_wiki_docs.py ./docs --pattern "*.md"

  # Dry run (scan without creating)
  python scripts/batch_create_wiki_docs.py ./docs --space-id 74812***88644 --dry-run
        """,
    )
    parser.add_argument(
        "folder",
        help="Path to folder with markdown files",
    )
    parser.add_argument(
        "--space-id",
        help="Target Wiki space ID (use --list-spaces or --personal)",
    )
    parser.add_argument(
        "--personal",
        action="store_true",
        help="Use personal knowledge base (auto-detects space_id)",
    )
    parser.add_argument(
        "--parent-token",
        help="Parent node token (creates at root if not provided)",
    )
    parser.add_argument(
        "--pattern",
        default="*.md",
        help="File glob pattern (default: *.md)",
    )
    parser.add_argument(
        "--app-id",
        help="Feishu app ID (or set FEISHU_APP_ID env var)",
    )
    parser.add_argument(
        "--app-secret",
        help="Feishu app secret (or set FEISHU_APP_SECRET env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan files without creating documents",
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

    # Validate space_id
    space_id = args.space_id
    if args.personal:
        # Auto-detect personal space
        client = FeishuApiClient.from_env() if not args.app_id else FeishuApiClient(args.app_id, args.app_secret)
        try:
            root_info = client.get_root_folder_info()
            my_library = root_info.get("my_library", {})
            if my_library:
                space_id = my_library.get("space_id")
                logger.info(f"Using personal knowledge base: space_id={space_id}")
            else:
                logger.error("Personal knowledge base not found. Please use --space-id instead.")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to detect personal space: {e}")
            sys.exit(1)

    if not space_id:
        logger.error("Must specify --space-id or --personal")
        sys.exit(1)

    # Execute batch creation
    logger.info(f"Scanning folder: {args.folder}")
    logger.info(f"Pattern: {args.pattern}")
    logger.info(f"Target space: {space_id}")
    if args.parent_token:
        logger.info(f"Parent node: {args.parent_token}")

    result = batch_create_wiki_docs(
        folder_path=args.folder,
        space_id=space_id,
        parent_token=args.parent_token,
        pattern=args.pattern,
        app_id=args.app_id,
        app_secret=args.app_secret,
        dry_run=args.dry_run,
    )

    # Output summary
    print("\n" + "=" * 60)
    print("📊 Batch Wiki Creation Summary")
    print("=" * 60)
    print(f"Total Files:    {result['total_files']}")
    print(f"✅ Successful:  {result['successful']}")
    print(f"❌ Failed:      {result['failed']}")
    print(f"Space ID:      {result['space_id']}")

    if result["successful"] > 0:
        print("\n📄 Created Wiki Nodes:")
        for r in result["results"]:
            if r["status"] == "success":
                print(f"  • {r['title']}")
                print(f"    URL: {r['url']}")
                print(f"    Blocks: {r.get('blocks', 0)}, Images: {r.get('images', 0)}")

    if result["failed"] > 0:
        print("\n❌ Failed Files:")
        for r in result["results"]:
            if "failed" in r["status"]:
                print(f"  • {r.get('title', r.get('file', 'unknown'))}")
                print(f"    Reason: {r['status']}")

    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if result["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
