#!/usr/bin/env python3
"""
Markdown to Feishu Uploader - Direct API Mode

This script uploads Markdown files to Feishu documents using direct API calls,
without going through MCP/AI. This is faster and more efficient for batch uploads.

Usage:
    # Set environment variables
    export FEISHU_APP_ID=cli_xxxxx
    export FEISHU_APP_SECRET=xxxxx

    # Upload directly
    uv run uv run python scripts/md_to_feishu_upload.py README.md doxcnxxxxx

    # Or use JSON mode (for AI/MCP workflow)
    uv run uv run python scripts/md_to_feishu_upload.py README.md doxcnxxxxx --mode json
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.md_to_feishu import MarkdownToFeishuConverter
from lib.feishu_api_client import (
    FeishuApiClient,
    FeishuApiClientError,
    upload_markdown_to_feishu
)


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def upload_direct(
    md_file: Path,
    doc_id: str,
    batch_size: int = 200,
    image_mode: str = 'local',
    app_id: str = None,
    app_secret: str = None
) -> dict:
    """
    Upload Markdown directly to Feishu using API.

    Args:
        md_file: Path to Markdown file
        doc_id: Feishu document ID
        batch_size: Blocks per batch
        image_mode: Image handling mode
        app_id: Feishu app ID (or use env var)
        app_secret: Feishu app secret (or use env var)

    Returns:
        Upload result dict
    """
    logger.info("Mode: Direct API Upload")
    logger.info(f"Markdown file: {md_file}")
    logger.info(f"Document ID: {doc_id}")

    # Step 1: Convert Markdown to blocks
    logger.info("Step 1: Converting Markdown to blocks...")
    converter = MarkdownToFeishuConverter(
        md_file=md_file,
        doc_id=doc_id,
        batch_size=batch_size,
        image_mode=image_mode
    )

    conversion_result = converter.convert()

    if not conversion_result.get("success"):
        raise RuntimeError(
            f"Failed to convert Markdown: {conversion_result.get('error', 'Unknown error')}"
        )

    blocks_count = len(conversion_result.get("blocks", []))
    batches_count = len(conversion_result.get("batches", []))
    images_count = len(conversion_result.get("images", []))

    logger.info(f"  → Converted {blocks_count} blocks in {batches_count} batches")
    logger.info(f"  → Found {images_count} images")

    # Step 2: Upload to Feishu
    logger.info("Step 2: Uploading to Feishu...")

    if app_id and app_secret:
        result = upload_markdown_to_feishu(
            md_file=str(md_file),
            doc_id=doc_id,
            app_id=app_id,
            app_secret=app_secret
        )
    else:
        result = upload_markdown_to_feishu(
            md_file=str(md_file),
            doc_id=doc_id
        )

    logger.info(f"  → Uploaded {result['total_blocks']} blocks")
    logger.info(f"  → Uploaded {result['total_images']} images")
    logger.info(f"  → Document: {result['document_url']}")

    return result


def upload_json(
    md_file: Path,
    doc_id: str,
    output: Path,
    batch_size: int = 200,
    image_mode: str = 'local'
) -> dict:
    """
    Convert Markdown to JSON (for AI/MCP workflow).

    Args:
        md_file: Path to Markdown file
        doc_id: Feishu document ID
        output: Output JSON file path
        batch_size: Blocks per batch
        image_mode: Image handling mode

    Returns:
        Conversion result dict
    """
    logger.info("Mode: JSON (for AI/MCP workflow)")
    logger.info(f"Markdown file: {md_file}")
    logger.info(f"Document ID: {doc_id}")
    logger.info(f"Output: {output}")

    # Convert using existing script
    converter = MarkdownToFeishuConverter(
        md_file=md_file,
        doc_id=doc_id,
        batch_size=batch_size,
        image_mode=image_mode
    )

    result = converter.convert()

    # Write to file
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"Output written to: {output}")

    return result


def print_env_help():
    """Print help for setting up environment variables"""
    print("\n" + "=" * 60)
    print("Environment Variables Setup")
    print("=" * 60)
    print("\nFor Direct API mode, you need to set:")
    print()
    print("  export FEISHU_APP_ID=cli_xxxxx")
    print("  export FEISHU_APP_SECRET=xxxxx")
    print()
    print("Get credentials from:")
    print("  1. https://open.feishu.cn/open-apis/app_modal")
    print("  2. Create a 'Self-built App' (自建应用)")
    print("  3. Copy App ID and App Secret")
    print()
    print("Required permissions:")
    print("  ✓ docx:document")
    print("  ✓ docx:document:create")
    print("  ✓ drive:file:upload")
    print("  ✓ See: https://github.com/cso1z/Feishu-MCP/blob/main/FEISHU_CONFIG.md")
    print()
    print("=" * 60)


def print_result(result: dict):
    """Print upload result"""
    print("\n" + "=" * 60)
    print("UPLOAD RESULT")
    print("=" * 60)

    if result.get("success"):
        print(f"\n✅ Success!")
        print(f"\nDocument URL: {result.get('document_url', 'N/A')}")
        print(f"Total blocks: {result.get('total_blocks', 0)}")
        print(f"Total images: {result.get('total_images', 0)}")
        print(f"Total batches: {result.get('total_batches', 0)}")
    else:
        print(f"\n❌ Failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Upload Markdown to Feishu (Direct API or JSON mode)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Direct upload (default, requires FEISHU_APP_ID and FEISHU_APP_SECRET)
  export FEISHU_APP_ID=cli_xxxxx
  export FEISHU_APP_SECRET=xxxxx
  python %(prog)s README.md doxcnxxxxx

  # JSON mode (for AI/MCP workflow)
  python %(prog)s README.md doxcnxxxxx --mode json

  # With custom batch size
  python %(prog)s README.md doxcnxxxxx --batch-size 50

  # Skip images
  python %(prog)s README.md doxcnxxxxx --image-mode skip
        """
    )

    parser.add_argument('md_file', type=Path, help='Path to Markdown file')
    parser.add_argument('doc_id', type=str, help='Feishu document ID (doxcnxxxxx)')
    parser.add_argument('--mode', choices=['direct', 'json'], default='direct',
                        help='Upload mode: direct (API) or json (for AI/MCP)')
    parser.add_argument('--output', type=Path, default=Path('/tmp/feishu_blocks.json'),
                        help='Output JSON file (only for json mode)')
    parser.add_argument('--batch-size', type=int, default=200,
                        help='Blocks per batch (default: 200)')
    parser.add_argument('--image-mode', choices=['local', 'download', 'skip'], default='local',
                        help='Image handling mode (default: local)')
    parser.add_argument('--app-id', type=str,
                        help='Feishu app ID (or use FEISHU_APP_ID env var)')
    parser.add_argument('--app-secret', type=str,
                        help='Feishu app secret (or use FEISHU_APP_SECRET env var)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--help-env', action='store_true',
                        help='Show help for setting up environment variables')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Show env help and exit
    if args.help_env:
        print_env_help()
        sys.exit(0)

    # Validate markdown file
    if not args.md_file.exists():
        print(f"Error: File not found: {args.md_file}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.mode == 'direct':
            # Direct API upload
            result = upload_direct(
                md_file=args.md_file,
                doc_id=args.doc_id,
                batch_size=args.batch_size,
                image_mode=args.image_mode,
                app_id=args.app_id,
                app_secret=args.app_secret
            )
            print_result(result)

        else:  # json mode
            # JSON output for AI/MCP workflow
            result = upload_json(
                md_file=args.md_file,
                doc_id=args.doc_id,
                output=args.output,
                batch_size=args.batch_size,
                image_mode=args.image_mode
            )

            # Print result to stdout
            print(json.dumps({
                'success': True,
                'output': str(args.output),
                'metadata': result.get('metadata')
            }, ensure_ascii=False, indent=2))

    except FeishuApiClientError as e:
        print(f"\n❌ API Error: {e}", file=sys.stderr)
        print("\n💡 Troubleshooting:", file=sys.stderr)
        print("  1. Check FEISHU_APP_ID and FEISHU_APP_SECRET are set correctly", file=sys.stderr)
        print("  2. Verify your Feishu app has required permissions", file=sys.stderr)
        print("  3. Check document ID is correct", file=sys.stderr)
        print("  4. Run with --help-env for setup instructions", file=sys.stderr)
        sys.exit(1)

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}", file=sys.stderr)
        print("\n💡 Solution:", file=sys.stderr)
        print("  Set environment variables:", file=sys.stderr)
        print("    export FEISHU_APP_ID=cli_xxxxx", file=sys.stderr)
        print("    export FEISHU_APP_SECRET=xxxxx", file=sys.stderr)
        print("  Or use --app-id and --app-secret arguments", file=sys.stderr)
        print("  Run with --help-env for setup instructions", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
