#!/usr/bin/env python3
"""
Get comprehensive Feishu workspace information.

This script retrieves:
- Root folder info (user's cloud drive root)
- All wiki spaces
- My Library (personal knowledge base)

Similar to feishu-docker MCP's get_feishu_root_folder_info tool.
"""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.feishu_api_client import FeishuApiClient, FeishuApiClientError

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def get_comprehensive_info():
    """Get comprehensive Feishu workspace information."""
    try:
        # Initialize client
        client = FeishuApiClient.from_env()

        print("=" * 70)
        print("📂 飞书工作区信息")
        print("=" * 70)

        # Use the new get_comprehensive_info method
        result = client.get_comprehensive_info()

        # Pretty print results
        print("\n📁 根文件夹:")
        if "error" in result["root_folder"]:
            print(f"  ✗ Error: {result['root_folder']['error']}")
        else:
            print(f"  ✓ Token: {result['root_folder'].get('token')}")
            print(f"  ✓ User ID: {result['root_folder'].get('user_id')}")

        print("\n📚 知识空间:")
        print(f"  ✓ 共 {len(result['wiki_spaces'])} 个空间:")
        for space in result["wiki_spaces"]:
            print(f"    - {space.get('name')} ({space.get('space_type')})")

        print("\n📖 我的知识库:")
        if "error" in result["my_library"]:
            print(f"  ✗ Error: {result['my_library']['error']}")
        else:
            print(f"  ✓ Space ID: {result['my_library'].get('space_id')}")
            print(f"  ✓ Name: {result['my_library'].get('name')}")

        print("\n" + "=" * 70)
        print("✅ 完整 JSON 信息:")
        print("=" * 70)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        return result

    except FeishuApiClientError as e:
        logger.error(f"API Error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


if __name__ == "__main__":
    result = get_comprehensive_info()
    sys.exit(0 if result else 1)
