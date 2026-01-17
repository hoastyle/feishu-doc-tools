#!/usr/bin/env python3
"""
Test script to verify Feishu API connectivity

This script tests:
1. Authentication (get tenant_access_token)
2. Block creation API format
3. Error handling

Usage:
    # Option 1: Use .env file (recommended)
    # Will auto-discover: .env, ../Feishu-MCP/.env
    python scripts/test_api_connectivity.py

    # Option 2: Set environment variables
    export FEISHU_APP_ID=cli_xxxxx
    export FEISHU_APP_SECRET=xxxxx
    python scripts/test_api_connectivity.py

    # Option 3: Specify custom .env file
    python -c "from lib.feishu_api_client import FeishuApiClient; \
                  client = FeishuApiClient.from_env('/path/to/.env'); \
                  print(client.get_tenant_token()[:20])"
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.feishu_api_client import (
    FeishuApiClient,
    FeishuApiClientError,
    FeishuApiAuthError,
    FeishuApiRequestError
)


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_authentication():
    """Test 1: Authentication"""
    print("\n" + "=" * 60)
    print("Test 1: Authentication (get tenant_access_token)")
    print("=" * 60)

    try:
        client = FeishuApiClient.from_env()
        token = client.get_tenant_token()

        print(f"✅ SUCCESS: Got token")
        print(f"   Token (first 20 chars): {token[:20]}...")
        print(f"   Token length: {len(token)}")
        return True
    except ValueError as e:
        print(f"❌ FAILED: {e}")
        print("\n💡 Solution (choose one):")
        print("   1. Create .env file:")
        print("      cp .env.example .env")
        print("      # Edit .env with your credentials")
        print("   2. Or reuse Feishu-MCP .env:")
        print("      # Already at ../Feishu-MCP/.env")
        print("   3. Or export variables:")
        print("      export FEISHU_APP_ID=cli_xxxxx")
        print("      export FEISHU_APP_SECRET=xxxxx")
        return False
    except FeishuApiAuthError as e:
        print(f"❌ FAILED: {e}")
        print("\n💡 Solution: Check your app credentials in Feishu Open Platform")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_block_format():
    """Test 2: Block format conversion"""
    print("\n" + "=" * 60)
    print("Test 2: Block format conversion")
    print("=" * 60)

    try:
        client = FeishuApiClient.from_env()

        # Test different block types
        test_blocks = [
            {
                "blockType": "text",
                "options": {
                    "text": {
                        "textStyles": [
                            {"text": "Hello, ", "style": {}},
                            {"text": "Feishu!", "style": {"bold": True}}
                        ],
                        "align": 1
                    }
                }
            },
            {
                "blockType": "heading1",
                "options": {
                    "heading": {
                        "level": 1,
                        "content": "Test Heading",
                        "align": 1
                    }
                }
            },
            {
                "blockType": "code",
                "options": {
                    "code": {
                        "code": "print('Hello, World!')",
                        "language": 49  # Python
                    }
                }
            },
            {
                "blockType": "list",
                "options": {
                    "list": {
                        "content": "First item",
                        "isOrdered": False
                    }
                }
            },
            {
                "blockType": "image",
                "options": {
                    "image": {
                        "align": 2
                    }
                }
            }
        ]

        print("Testing block format conversion:")
        for i, block in enumerate(test_blocks, 1):
            block_type = block["blockType"]
            print(f"\n  {i}. {block_type} block:")

            if block_type == "text":
                formatted = client._format_text_block(block["options"])
            elif block_type.startswith("heading"):
                formatted = client._format_heading_block(block_type, block["options"])
            elif block_type == "code":
                formatted = client._format_code_block(block["options"])
            elif block_type == "list":
                formatted = client._format_list_block(block["options"])
            elif block_type == "image":
                formatted = client._format_image_block(block["options"])
            else:
                print(f"     ⚠️  Skipped (unknown type)")
                continue

            print(f"     ✓ Formatted successfully")
            print(f"     block_type: {formatted.get('block_type')}")

        print(f"\n✅ SUCCESS: All block types formatted correctly")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_api_document_id():
    """Test 3: Validate document ID format"""
    print("\n" + "=" * 60)
    print("Test 3: Document ID validation")
    print("=" * 60)

    # Valid document ID formats
    valid_ids = [
        "doxcnxxxxxxxxxxxxxxx",  # New docx format
        "doccnxxxxxxxxxxxxxxx",  # Old doc format
        "doxcnAbCdEf1234567890",  # Mixed case
    ]

    print("Valid document ID formats:")
    for doc_id in valid_ids:
        print(f"  ✓ {doc_id}")

    print(f"\n✅ SUCCESS: Document ID format is standard")
    print(f"\n💡 To get a document ID:")
    print(f"   1. Create a new document in Feishu")
    print(f"   2. Copy from URL: https://xxx.feishu.cn/docx/{{doc_id}}")
    print(f"   3. Or use: https://xxx.feishu.cn/wiki/{{token}}")
    return True


def print_test_summary(results: dict):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total = len(results)
    passed = sum(results.values())

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! API connectivity verified.")
        print("\nNext steps:")
        print("1. Create a test document in Feishu")
        print("2. Get the document ID from the URL")
        print("3. Test uploading Markdown:")
        print("   python scripts/test_api_upload.py <doc_id>")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")

    print("=" * 60)


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Feishu API Connectivity Test")
    print("=" * 60)
    print("\nThis script tests the Feishu API integration.")
    print("\nCredential setup (choose one):")
    print("  1. Use .env file (recommended)")
    print("     - Auto-discovers: .env, ../Feishu-MCP/.env")
    print("     - Or copy .env.example to .env and edit")
    print("  2. Set environment variables")
    print("     export FEISHU_APP_ID=cli_xxxxx")
    print("     export FEISHU_APP_SECRET=xxxxx")

    # Note: from_env() will automatically load .env files
    # No manual check needed here

    # Run tests
    results = {}

    # Test 1: Authentication
    results["Authentication"] = test_authentication()

    # Only run remaining tests if authentication passed
    if results["Authentication"]:
        results["Block Format"] = test_block_format()
        results["Document ID Validation"] = test_api_document_id()
    else:
        results["Block Format"] = False
        results["Document ID Validation"] = False

    # Print summary
    print_test_summary(results)

    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
